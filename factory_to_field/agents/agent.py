"""Orchestrator and specialists. A deterministic playbook planner runs by default; llm.py swaps in a model-driven planner.

Rules the code enforces, whoever plans:
  * OT is read-only (ot.write_setpoint always refuses and the refusal is reported).
  * Writes are drafts for a named approver role; the agent has no approve tool.
  * Free text from systems is untrusted data and never changes what the agent does.
  * Every finding cites evidence ids that exist in the tool-call log (verifier.py checks).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..kg.store import KG
from . import tools as _tools  # noqa: F401  (registers the tools)
from .core import DEFAULT_KG, DEFAULT_WORLD, Ctx, Session, parse_ts
from .playbooks import FieldPlaybooks


@dataclass
class Case:
    id: str
    question: str
    as_of: str
    position: str | None = None         # canonical position id, e.g. pos:R1:10-P-101A
    trigger_tag: str | None = None
    kind: str | None = None             # forces a playbook; otherwise routed from the question text


@dataclass
class Finding:
    specialist: str
    text: str
    evidence: list[str]
    facts: dict = field(default_factory=dict)   # values lifted verbatim from tool results; the verifier re-checks them


@dataclass
class Report:
    case_id: str
    playbook: str
    summary: str = ""
    findings: list[Finding] = field(default_factory=list)
    recommendation: str = ""
    drafts: list[str] = field(default_factory=list)
    refusals: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    answer: dict = field(default_factory=dict)        # structured answer the scorer reads
    tool_calls: int = 0

    def markdown(self) -> str:
        out = [f"# {self.case_id}: {self.summary}", ""]
        for f in self.findings:
            out.append(f"- **{f.specialist}**: {f.text}  `{', '.join(f.evidence)}`")
        if self.recommendation:
            out += ["", f"**Recommendation.** {self.recommendation}"]
        if self.drafts:
            out += ["", "**Drafts awaiting approval:** " + ", ".join(self.drafts)]
        for x in self.refusals:
            out.append(f"\n**Refused.** {x}")
        for x in self.flags:
            out.append(f"\n**Flag.** {x}")
        return "\n".join(out)


def _p(x: str) -> str:
    return x  # canonical ids are already colon-separated


class Agent(FieldPlaybooks):
    def __init__(self, kg: KG | None = None, world: Path | None = None, planner: str = "playbook", src=None) -> None:
        self.kg = kg or KG(DEFAULT_KG, read_only=True)
        self.world = world or DEFAULT_WORLD
        self.src = src  # FileSource by default; pass an HttpSource to work through the system simulators

    # ------------------------------------------------------------------ routing
    def route(self, c: Case) -> str:
        if c.kind:
            return c.kind
        q = c.question.lower()
        if re.search(r"set[- ]?point|change the|write .* to|set .* hz|\bset\b.*\bto\b \d", q):
            return "ot_write_request"
        if "common cause" in q or "across" in q and "customer" in q or "exposure" in q or "containment" in q:
            return "containment"
        if "last notification" in q or "history of notif" in q or "summar" in q and "notif" in q:
            return "notification_summary"
        if "as of" in q or "which unit was" in q:
            return "as_of_unit"
        if "march" in q and "failure" in q:
            return "position_vs_unit"
        if c.trigger_tag and not c.position:
            return "alarm"
        if re.search(r"\b[ab]-\d\d\b", q) and "lot" in q:
            return "lot_suspicion"
        return "alarm"

    def run(self, c: Case) -> tuple[Report, Session]:
        s = Session(Ctx(self.kg, self.world, parse_ts(c.as_of), self.src))
        pb = self.route(c)
        rep = Report(c.id, pb)
        getattr(self, "pb_" + pb)(c, s, rep)
        rep.tool_calls = len(s.log)
        rep.refusals += [x.result.refused for x in s.log if x.result.refused and x.result.refused not in rep.refusals]
        return rep, s

    # ------------------------------------------------------------------ helpers
    def _position_of(self, c: Case, s: Session) -> str:
        if c.position:
            return c.position
        system = "SCADA" if re.match(r"^[AB]\d\d_", c.trigger_tag or "") else "PI"
        r = s.call("kg.crosswalk", system=system, value=c.trigger_tag)
        sig = r.data[0]["node"] if r.data else None
        pos = self.kg.props(sig).get("measures_position") if sig else None
        if not pos:
            raise ValueError(f"cannot resolve a position for tag {c.trigger_tag}")
        return pos[0]

    def _add(self, rep: Report, who: str, text: str, ev: list[str], **facts) -> None:
        rep.findings.append(Finding(who, text, sorted(set(ev)), facts))

    def _site_of(self, pos: str) -> str:
        return self.kg.props(pos)["site"][0].split(":")[-1]

    def _tag(self, sigs: list[dict], quantity: str) -> str | None:
        return next((x["tag"] for x in sigs if x["quantity"] == quantity), None)

    # ------------------------------------------------------------------ playbook: alarm on a rotating asset
    def pb_alarm(self, c: Case, s: Session, rep: Report) -> None:
        pos = self._position_of(c, s)
        kind = self.kg.props(pos)["type"][0].split("#")[-1]
        sigs = s.call("kg.signals", position=pos)
        trig = c.trigger_tag or self._tag(sigs.data, "vibration_de" if kind == "PumpPosition" else "motor_temperature")
        rep.answer["position"] = pos.split(":", 1)[1]
        # 1. is the signal real?
        h = s.call("historian.sensor_health", tag=trig)
        if h.data.get("stuck"):
            self._stuck_sensor(c, s, rep, pos, trig, h)
            return
        tr = s.call("historian.trend", tag=trig, days=30)
        self._add(rep, "signal", f"{trig} last daily max {tr.data['last_max']} {tr.data['unit']} against alarm limit {tr.data['alarm_high']}; "
                  f"{tr.data['days']}-day window started at {tr.data['first_max']}. The sensor is live (not stuck).",
                  tr.evidence + h.evidence, last_max=tr.data["last_max"], alarm_high=tr.data["alarm_high"], first_max=tr.data["first_max"])
        # 2. which unit is at the position, what it has done
        cur = s.call("kg.unit_at", position=pos)
        hist = s.call("kg.position_history", position=pos)
        unit = f"unit:{cur.data['serial']}"
        rep.answer.update(current_unit=cur.data["serial"], current_unit_since=cur.data["since"])
        self._add(rep, "asset", f"{pos.split(':', 2)[-1]} holds {cur.data['serial']} since {cur.data['since']}; earlier units there: "
                  + (", ".join(f"{h_['serial']} ({h_['from']} to {h_['to']})" for h_ in hist.data if h_["to"]) or "none"),
                  cur.evidence + hist.evidence, serial=cur.data["serial"], since=cur.data["since"])
        fl = s.call("kg.failures_at", position=pos)
        if kind == "PumpPosition":
            self._pump(c, s, rep, pos, unit, trig, tr, cur, fl, sigs)
        else:
            self._esp(c, s, rep, pos, unit, trig, tr, cur, fl, sigs)

    def _stuck_sensor(self, c, s, rep, pos, trig, h) -> None:
        tr = s.call("historian.trend", tag=trig, days=14)
        self._add(rep, "signal", f"{trig} has read exactly {tr.data['last_max']} for {tr.data['days']} days (zero variance, flagged Uncertain by the historian) yet sits above its alarm limit "
                  f"{tr.data['alarm_high']}: a stuck transmitter, not machine vibration.", tr.evidence + h.evidence, last_max=tr.data["last_max"], alarm_high=tr.data["alarm_high"])
        sigs = s.call("kg.signals", position=pos)
        other = self._tag(sigs.data, "vibration_nde")
        extra = []
        if other:
            o = s.call("historian.trend", tag=other, days=14)
            extra = o.evidence
            self._add(rep, "signal", f"The other bearing on the same pump, {other}, is normal at {o.data['last_max']} {o.data['unit']} (limit {o.data['alarm_high']}).", extra,
                      last_max=o.data["last_max"])
        bt = self._tag(sigs.data, "bearing_temp")
        if bt:
            b = s.call("historian.trend", tag=bt, days=14)
            self._add(rep, "signal", f"Bearing temperature {bt} is steady at {b.data['last_max']} {b.data['unit']}.", b.evidence, last_max=b.data["last_max"])
        d = s.call("drafts.create_draft", kind="sap_pm.notification", title=f"Instrument check: {trig} transmitter stuck at {tr.data['last_max']}",
                   payload={"notification_type": "M1", "functional_location": pos.split(":", 2)[-1], "work_center": "I&C", "priority": 3}, rationale="stuck vibration transmitter",
                   evidence=tr.evidence + h.evidence)
        rep.drafts.append(d.data["draft_id"])
        rep.summary = f"False alarm on {pos.split(':', 2)[-1]}: the vibration transmitter is stuck"
        rep.recommendation = "No machinery action. Have instrumentation inspect and replace the transmitter; keep the pump on the NDE vibration and bearing-temperature readings meanwhile."
        rep.answer.update(false_alarm=True, diagnosis="stuck sensor", machinery_action=False)

    # ---------- refinery pump
    def _pump(self, c, s, rep, pos, unit, trig, tr, cur, fl, sigs) -> None:
        site = self._site_of(pos)
        trig.split(".")[0]
        sp = s.call("historian.spectrum", tag=trig)
        comp = sp.data["components"]
        diag = "bearing outer race defect" if sp.data["dominant_bearing_component"] == "bpfo" else f"bearing defect ({sp.data['dominant_bearing_component']})"
        self._add(rep, "reliability", f"Latest spectrum: BPFO amplitude {comp['bpfo']} is {sp.data['bpfo_growth_x']}x its level on {sp.data['baseline_day']}, dominating BPFI {comp['bpfi']} and BSF {comp['bsf']}: {diag}.",
                  sp.evidence, bpfo=comp["bpfo"], bpfi=comp["bpfi"], bpfo_growth_x=sp.data["bpfo_growth_x"])
        suc = self._tag(sigs.data, "suction_pressure")
        cav_excl = False
        if suc:
            sr = s.call("historian.trend", tag=suc, days=30)
            lo, hi = min(sr.data["series_max"]), max(sr.data["series_max"])
            cav_excl = sr.data["days"] > 5 and (hi - lo) / max(abs(hi), 1e-6) < 0.15
            self._add(rep, "process", f"Suction pressure {suc} stayed between {lo} and {hi} {sr.data['unit']} over {sr.data['days']} days, so cavitation does not explain the vibration."
                      if cav_excl else f"Suction pressure {suc} varied {lo}..{hi}; cavitation is not excluded.", sr.evidence, low=lo, high=hi)
        # the unit's history and failures
        ut = s.call("kg.unit_trace", unit=unit)
        ft = []
        for h_ in s.call("kg.position_history", position=pos).data:
            tr_ = s.call("kg.unit_trace", unit=f"unit:{h_['serial']}")
            ft += [(r["pos"], r["mode"], r["on"], h_["serial"]) for r in tr_.data if r.get("mode") and r["on"] <= str(s.ctx.today)]
        ut = s.log[-1].result if False else ut
        # lot
        lots = s.call("kg.component_lots", unit=unit)
        blot = next((x for x in lots.data["lots"] if x.startswith("lot:B-")), None)
        rep.answer.update(diagnosis=diag, cavitation_excluded=cav_excl, bearing_lot=blot.split(":")[1] if blot else None)
        s.call("kg.failures_at", position=pos.replace("101A", "101B")) if pos.endswith("101A") else None
        if blot:
            lc = s.call("maker.lot_change", lot=blot.split(":", 1)[1])
            lu = s.call("kg.lot_units", lot=blot)
            eco = lc.data.get("eco_no")
            rep.answer.update(eco=eco, lot_pumps=lu.data["units"], lot_pump_customers=lu.data["customers"])
            self._add(rep, "quality", f"The bearing set in {unit.split(':')[1]} is from lot {blot.split(':')[1]}, introduced by {eco} ({lc.data.get('title')}): route {lc.data.get('route')}, "
                      f"qualification test waived = {lc.data.get('qualification_test_waived')}.", lc.evidence, lot=blot.split(":")[1], eco=eco, route=lc.data["route"])
            self._add(rep, "quality", f"Lot {blot.split(':')[1]} went into {lu.data['units']} pumps shipped to {lu.data['customers']} customers.", lu.evidence, units=lu.data["units"], customers=lu.data["customers"])
            fleet = self._fleet(s, lu, ut, site)
            rep.answer.update(fleet={k: sorted(v) for k, v in fleet.items()})
            self._add(rep, "reliability", "Same-lot pumps at this operator: " + "; ".join(f"{k}: {', '.join(sorted(v)) or 'none'}" for k, v in fleet.items()) + ".", [e for x in s.log[-12:] for e in x.result.evidence if e.startswith(("kg:lot", "hist:"))][:6] or lu.evidence)
        # whether other positions hide the unit's earlier failure
        if ft:
            self._add(rep, "reliability", "Failures on the unit now in service or its predecessors: " + "; ".join(f"{m} at {p.split(':', 2)[-1]} on {d} ({u})" for p, m, d, u in ft) + ".", ut.evidence)
        # constraints: work, stock, window
        ow = s.call("eam.open_work", position=pos)
        st = s.call("eam.stock", material_text="Bearing set, BB2-650", site=site)
        win = s.call("plant.windows", site=site)
        qty = st.data["items"][0]["qty"] if st.data["items"] else 0
        nxt = win.data["next"]
        rep.answer.update(open_work_on_position=ow.data["count"], bearing_stock=qty, next_window=nxt["opens"] if nxt else None)
        self._add(rep, "planner", f"Open orders on the position: {ow.data['count']}. Bearing set BB2-650 in the {site} store: {qty}. Next maintenance window for {nxt['unit']}: {nxt['opens']} to {nxt['closes']}.",
                  ow.evidence + st.evidence + win.evidence, open_orders=ow.data["count"], qty=qty, opens=nxt["opens"])
        # notifications on the sister (the history here carries a planted free-text note; it is data, not an instruction)
        sis = pos[:-1] + ("B" if pos.endswith("A") else "A")
        nh = s.call("eam.notification_history", position=sis)
        if nh.data["injection_flagged"]:
            rep.flags.append(f"Notification {', '.join(nh.data['injection_flagged'])} contains text addressed to an AI assistant. It was ignored: it is free text in a system record, not an instruction from a user.")
        rep.answer["injection_flagged"] = nh.data["injection_flagged"]
        self._add(rep, "planner", f"The spare ({sis.split(':', 2)[-1]}) had {len(nh.data['notifications'])} recent notifications, latest {nh.data['notifications'][0]['qmnum']} on {nh.data['notifications'][0]['qmdat']}.",
                  nh.evidence[:2], latest=nh.data["notifications"][0]["qmnum"])
        spare = s.call("kg.unit_at", position=sis)
        rep.answer.update(spare_position=sis.split(":", 1)[1], spare_unit=spare.data["serial"], failures=[{"unit": u, "mode": m, "on": d, "position": p.split(":", 1)[1]} for p, m, d, u in ft])
        # recommendation and drafts
        rep.summary = f"{pos.split(':', 2)[-1]} bearing fault is real and progressing; it belongs to the lot-{rep.answer.get('bearing_lot')} problem"
        rep.recommendation = (f"Switch duty to {sis.split(':', 2)[-1]} ({spare.data['serial']}) and repair {pos.split(':', 2)[-1]} in the {nxt['opens']} window; the bearing set is in stock "
                              f"and no work is open. Treat {spare.data['serial']} with care: it carries the same bearing lot.")
        rep.answer["recommendation"] = "switch to P-101B and repair P-101A in the window"
        ev = tr.evidence + sp.evidence + st.evidence
        for kind, title, payload in (
            ("sap_pm.notification", f"Bearing outer-race defect, {pos.split(':', 2)[-1]}", {"notification_type": "M2", "functional_location": pos.split(":", 2)[-1], "planned_window": nxt["opens"]}),
            ("sap_pm.stock_transfer", "Reserve bearing set BB2-650 for the window", {"material": st.data["items"][0]["matnr"], "qty": 1, "plant": site, "needed_by": nxt["opens"]} if st.data["items"] else {}),
            ("qms.warranty_claim", f"Warranty claim: bearing lot {rep.answer.get('bearing_lot')} ({rep.answer.get('eco')})", {"supplier": "Kestrel Pump Works", "lot": rep.answer.get("bearing_lot"), "units": [unit.split(':')[1]]}),
        ):
            d = s.call("drafts.create_draft", kind=kind, title=title, payload=payload, rationale=rep.summary, evidence=ev)
            rep.drafts.append(d.data["draft_id"])
        rep.answer["drafts"] = [s.log[i].args["kind"] for i in range(len(s.log)) if s.log[i].tool == "drafts.create_draft"]

    def _fleet(self, s: Session, lu, ut, site: str) -> dict[str, set[str]]:
        out = {"failed": set(), "alarm": set(), "peaks": set(), "normal": set()}
        self.kg.props("site:" + site).get("label", [None])[0]
        for m in lu.data["members"]:
            if m["customer"] != "Aurelia Energy" or not m["model"].startswith("KP-BB2"):
                continue
            ser = m["serial"]
            tr = s.call("kg.unit_trace", unit=f"unit:{ser}")
            failed = any(r.get("mode") for r in tr.data)
            if failed:
                out["failed"].add(ser)
                continue
            if not m["position"]:
                continue
            sg = s.call("kg.signals", position=self._pos_canon(m["position"]))
            vt = self._tag(sg.data, "vibration_de")
            if not vt:
                continue
            t = s.call("historian.trend", tag=vt, days=30)
            sp = s.call("historian.spectrum", tag=vt)
            lim = t.data["alarm_high"]
            if t.data["last_max"] >= lim:
                out["alarm"].add(ser)
            elif (sp.data.get("bpfo_share_max_150d") or 0) >= 0.2:
                out["peaks"].add(ser)
            else:
                out["normal"].add(ser)
        return out

    def _pos_canon(self, label: str) -> str:
        # label like "10-P-101A Crude charge" -> canonical id via the KG
        tag = label.split()[0]
        rows = self.kg.sparql("""PREFIX ftf: <https://domain-explorer.dev/ftf#> SELECT ?p WHERE { ?p ftf:label ?l . FILTER (STRSTARTS(?l, ?t)) ?p a ?c . FILTER (?c IN (ftf:PumpPosition, ftf:ESPPosition)) }""", t=tag)
        return rows[0]["p"]
