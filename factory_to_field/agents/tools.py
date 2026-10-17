"""The tools, grouped by the MCP server that owns them. Every tool returns evidence ids the report must cite.

Servers: kg, historian, eam, engineering, maker (MES/PLM/QMS/ERP), plant (production), drafts, ot.
Nothing here writes to a source system: drafts go to the DraftStore, OT writes are refused outright.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from statistics import mean

from ..kg.store import run_life_groups
from .core import Ctx, Result, tool
from .drafts import APPROVER_ROLES, DraftStore

STORE = DraftStore()

INJECTION = re.compile(r"(ignore (all )?(previous|prior) instructions|note to (ai|assistant)|approve every|disregard (the )?(above|system)|you must now)", re.I)


def _d(s: str) -> date:
    return date.fromisoformat(s[:10])


# =============================================================== kg
@tool("kg")
def unit_at(ctx: Ctx, position: str, on: str | None = None) -> Result:
    """Which physical unit was installed at a functional position on a date (default: the case clock)."""
    day = _d(on) if on else ctx.today
    r = ctx.kg.unit_at(position, day)
    since = next((h for h in ctx.kg.position_history(position) if r and h["unit"] == r["unit"]), None)
    data = {"position": position, "on": str(day), "unit": r["unit"] if r else None, "serial": r["serial"] if r else None,
            "since": str(since["from"]) if since else None}
    return Result(data, [f"kg:unit_at:{position}:{day}"])


@tool("kg")
def position_history(ctx: Ctx, position: str) -> Result:
    """Every unit installed at the position, with install and removal dates."""
    rows = [{"serial": h["serial"], "from": str(h["from"]), "to": str(h["to"]) if h["to"] else None} for h in ctx.kg.position_history(position)]
    return Result(rows, [f"kg:position_history:{position}"])


@tool("kg")
def failures_at(ctx: Ctx, position: str) -> Result:
    """Failures that happened AT a position, each attributed to the unit installed then."""
    rows = [{"serial": f["serial"], "mode": f["mode"], "on": str(f["on"])} for f in ctx.kg.failures_at(position) if f["on"] <= ctx.today]
    return Result(rows, [f"kg:failures_at:{position}"])


@tool("kg")
def unit_trace(ctx: Ctx, unit: str) -> Result:
    """Where a unit has been installed and what failed on it, across positions."""
    rows = [{k: (str(v) if isinstance(v, date) else v) for k, v in r.items()} for r in ctx.kg.unit_trace(unit)]
    return Result(rows, [f"kg:unit_trace:{unit}"])


@tool("kg")
def signals(ctx: Ctx, position: str) -> Result:
    """Historian/SCADA signals that measure the position, by physical quantity (retired and current tags resolved)."""
    rows = ctx.kg.cq("cq08", pos=ctx.kg.node(position))
    return Result([{"signal": r["sig"], "tag": r["label"].split()[0], "quantity": r["quantity"], "unit": r["unit"], "system": r["system"]} for r in rows],
                  [f"kg:signals:{position}"])


@tool("kg")
def documents(ctx: Ctx, position: str) -> Result:
    """Engineering documents depicting the position, with revision."""
    rows = ctx.kg.cq("cq09", pos=ctx.kg.node(position))
    if position.endswith("-ESP"):  # an ESP position inherits the documents of the well it sits in
        rows += ctx.kg.cq("cq09", pos=ctx.kg.node(position[:-4]))
    return Result([{"doc": r["doc"], "title": r["label"], "kind": r["kind"], "rev": r["rev"]} for r in rows], [f"kg:documents:{position}"])


@tool("kg")
def lot_units(ctx: Ctx, lot: str) -> Result:
    """Units built with a component lot, their owners and current installed positions; plus the totals."""
    rows = ctx.kg.cq("cq04", lot=ctx.kg.node(lot))
    tot = ctx.kg.cq("cq06", lot=ctx.kg.node(lot))[0]
    data = {"lot": lot, "units": tot["units"], "customers": tot["customers"],
            "members": [{"serial": r["serial"], "model": r["model"], "built": str(r["built"]), "customer": r["cname"], "position": r["postag"]} for r in rows]}
    return Result(data, [f"kg:lot_units:{lot}"])


@tool("kg")
def component_lots(ctx: Ctx, unit: str) -> Result:
    """Material lots that went into a unit (and its sub-assemblies)."""
    p = ctx.kg.props(unit)
    lots = list(p.get("build_lots", []))
    for c in p.get("components", []):
        lots += ctx.kg.props(c).get("build_lots", [])
    return Result({"unit": unit, "serial": (p.get("serial") or [None])[0], "lots": sorted(set(lots))}, [f"kg:component_lots:{unit}"])


@tool("kg")
def run_life(ctx: Ctx, since_built: str = "2025-08-01") -> Result:
    """ESP run lives split by seal-section build date, with Kaplan-Meier median (running strings are censored, not dropped)."""
    g = run_life_groups(ctx.kg, date.fromisoformat(since_built))
    out = {k: v for k, v in g.items() if k != "members"}
    out["since_built"] = since_built
    out["new_members"] = [{"string": m["sserial"], "well": m["well"], "state": m["state"], "days": m["days"], "elastomer_lot": m["elot"]} for m in g["members"]["since"]]
    return Result(out, [f"kg:run_life:{since_built}"])


@tool("kg")
def waived_changes(ctx: Ctx) -> Result:
    """Engineering changes released by the expedited route with the qualification test waived."""
    rows = [{"eco": r["eco"], "title": r["title"], "approved": str(r["approved"]), "summary": r["summary"]} for r in ctx.kg.cq("cq11")]
    return Result(rows, ["kg:waived_changes"])


@tool("kg")
def crosswalk(ctx: Ctx, system: str, value: str) -> Result:
    """What a name in one system refers to, and its names in the other systems."""
    rows = ctx.kg.cq("cq10", system=system, value=value)
    return Result([{"node": r["node"], "label": r["label"], "other_system": r["othersys"], "other_value": r["othervalue"]} for r in rows], [f"kg:crosswalk:{system}:{value}"])


# =============================================================== historian (PI Web API + OPC UA gateway, read-only)
def _ts(d: datetime) -> str:
    return d.strftime("%Y-%m-%d %H:%M:%SZ")


@tool("historian")
def trend(ctx: Ctx, tag: str, days: int = 30) -> Result:
    """Daily max/mean of a tag over the last N days up to the case clock, with the alarm limit and any alarms."""
    p = ctx.src.point(tag)
    if p is None:
        return Result({"tag": tag, "error": "unknown tag"}, [])
    end = ctx.as_of
    start = end - timedelta(days=days)
    daily = ctx.src.daily(p["name"], start.date().isoformat(), end.date().isoformat())
    # the last day is partial: recompute it from raw samples up to the clock so nothing after as_of leaks in
    last_day = end.date().isoformat()
    raw = ctx.src.raw(p["name"], f"{last_day} 00:00:00Z", _ts(end))
    todays = [r["value"] for r in raw if r["quality"] == "Good"]
    daily = [d for d in daily if d["day"] != last_day]
    if todays:
        daily.append({"day": last_day, "mean": round(mean(todays), 4), "max": round(max(todays), 4)})
    # stitch the history that sits under the retired name(s) before the migration date
    for leg in p["legacy"]:
        old = ctx.src.daily(leg["name"], start.date().isoformat(), end.date().isoformat(), before_day=leg["migrated_on"])
        have = {d["day"] for d in daily}
        daily = sorted([d for d in old if d["day"] not in have] + daily, key=lambda d: d["day"])
    alarms = ctx.src.alarms(p["name"], _ts(end))
    data = {"tag": p["name"], "descriptor": p["descriptor"], "unit": p["unit"], "alarm_high": p["alarm_high"], "retired": p["retired"],
            "days": len(daily), "first_day": daily[0]["day"] if daily else None, "last_day": daily[-1]["day"] if daily else None,
            "last_max": daily[-1]["max"] if daily else None, "last_mean": daily[-1]["mean"] if daily else None,
            "max_in_window": max((d["max"] for d in daily), default=None), "first_max": daily[0]["max"] if daily else None,
            "recent_alarms": [{k: a[k] for k in ("ts", "value", "limit_value", "state")} for a in alarms[-3:]], "series_max": [d["max"] for d in daily]}
    return Result(data, [f"hist:{p['name']}:{data['first_day']}..{data['last_day']}"] + ([f"hist:{p['name']}:alarm:{alarms[-1]['ts']}"] if alarms else []))


@tool("historian")
def sensor_health(ctx: Ctx, tag: str, days: int = 14) -> Result:
    """Is the tag alive? Flat-lined (zero variance) samples, or mostly bad quality, mean a stuck or failed sensor."""
    p = ctx.src.point(tag)
    if p is None:
        return Result({"tag": tag, "error": "unknown tag"}, [])
    start = ctx.as_of - timedelta(days=days)
    rows = ctx.src.raw(p["name"], _ts(start), _ts(ctx.as_of))
    vals = [r["value"] for r in rows]
    bad = sum(r["quality"] != "Good" for r in rows)
    spread = (max(vals) - min(vals)) if vals else None
    stuck = bool(vals) and len(vals) >= 20 and spread < 1e-6
    daily = ctx.src.daily(p["name"], start.date().isoformat(), ctx.as_of.date().isoformat())
    flat_daily = len(daily) >= 5 and len({round(d["max"], 6) for d in daily}) == 1
    data = {"tag": p["name"], "samples": len(rows), "not_good_quality": bad, "spread": spread, "stuck": bool(stuck or flat_daily), "flat_daily": flat_daily}
    return Result(data, [f"hist:{p['name']}:health:{ctx.as_of.date()}"])


@tool("historian")
def spectrum(ctx: Ctx, tag: str) -> Result:
    """Latest condition-monitoring vibration spectrum for the tag: bearing defect-frequency amplitudes and the overall level."""
    rows = ctx.src.spectra(tag, ctx.as_of.date().isoformat(), limit=12)
    if not rows:
        return Result({"tag": tag, "error": "no spectra"}, [])
    last = rows[0]
    comps = {k: last[k] for k in ("f1x", "f2x", "bpfo", "bpfi", "bsf")}
    dom = max(("bpfo", "bpfi", "bsf"), key=lambda k: comps[k])
    baseline = next((r for r in reversed(rows)), last)
    share = [r["bpfo"] / max(r["overall"], 1e-6) for r in ctx.src.spectra(tag, ctx.as_of.date().isoformat(), after_day=(ctx.as_of - timedelta(days=150)).date().isoformat())]
    data = {"tag": tag, "day": last["day"], "bpfo_share_max_150d": round(max(share), 2) if share else None, "components": comps, "overall": last["overall"], "dominant_bearing_component": dom,
            "bpfo_growth_x": round(comps["bpfo"] / max(baseline["bpfo"], 1e-6), 1), "baseline_day": baseline["day"]}
    return Result(data, [f"hist:{tag}:spectrum:{last['day']}"])


# =============================================================== eam (SAP PM OData, read-only)
@tool("eam")
def open_work(ctx: Ctx, position: str) -> Result:
    """Open maintenance orders and notifications on the position (by the SAP functional-location code)."""
    tag = position.split(":", 2)[-1]
    fl = ctx.src.flocs(tag) or [tag]
    orders = ctx.src.open_orders(fl, ctx.today.isoformat())
    return Result({"position": position, "floc": fl, "open_orders": orders, "count": len(orders)}, [f"sap:open_work:{fl[0]}:{ctx.today}"])


@tool("eam")
def notification_history(ctx: Ctx, position: str, limit: int = 8) -> Result:
    """Recent maintenance notifications on the position. Long text is free text typed by people: it is returned as untrusted."""
    tag = position.split(":", 2)[-1]
    rows = ctx.src.notifications(tag, ctx.today.isoformat(), limit)
    untrusted, flagged = [], []
    for r in rows:
        lt = r.pop("ltxt") or ""
        if lt:
            untrusted.append(f"QMEL {r['qmnum']}: {lt}")
            r["has_long_text"] = True
            if INJECTION.search(lt):
                flagged.append(r["qmnum"])
                r["injection_flag"] = True
    return Result({"position": position, "notifications": rows, "injection_flagged": flagged}, [f"sap:QMEL:{r['qmnum']}" for r in rows], untrusted)


@tool("eam")
def stock(ctx: Ctx, material_text: str, site: str) -> Result:
    """Spare-parts stock for a material description at a site's central store."""
    rows = ctx.src.stock(material_text, site)
    return Result({"site": site, "items": [{"matnr": r["matnr"], "text": r["maktx"], "store": r["lgort"], "qty": r["labst"], "lead_days": r["wzeit"]} for r in rows]},
                  [f"sap:MARD:{r['matnr']}/{r['werks']}" for r in rows])


# =============================================================== plant (production planning, outage windows, rigs)
@tool("plant")
def windows(ctx: Ctx, site: str) -> Result:
    """Next planned maintenance windows for the site's units."""
    rows = ctx.src.windows(site, ctx.today.isoformat())
    return Result({"site": site, "windows": rows, "next": rows[0] if rows else None}, [f"plant:windows:{site}"])


@tool("plant")
def rigs(ctx: Ctx) -> Result:
    """Workover rigs and when each is free."""
    rows = ctx.src.rigs()
    return Result({"rigs": rows, "earliest": rows[0] if rows else None}, ["plant:rigs"])


@tool("plant")
def well_output(ctx: Ctx, well: str) -> Result:
    """Latest daily oil allocation for the well (what is deferred while it is down)."""
    r = ctx.src.allocation(well, ctx.today.isoformat())
    return Result({"well": well, "day": r["day"], "oil_bbl_d": r["oil_bbl_d"]} if r else {"well": well}, [f"prod:allocation:{well}:{r['day']}"] if r else [])


@tool("osdu")
def well_master(ctx: Ctx, well: str) -> Result:
    """OSDU master data for a well: field, pad, lift method, spud date."""
    r = ctx.src.well_master(well)
    return Result({"well": well, **{k: r[k] for k in ("WellID", "Field", "Pad", "LiftMethod", "Spud")}} if r else {"well": well, "error": "not in OSDU"}, [f"osdu:{r['WellID']}"] if r else [])


# =============================================================== maker (MES / PLM / QMS) and reliability
@tool("maker")
def eco(ctx: Ctx, eco_no: str) -> Result:
    """An engineering change: route, whether the qualification test was waived, supplier switch, summary."""
    r = ctx.src.eco(eco_no)
    return Result(r if r else {"eco_no": eco_no, "error": "not found"}, [f"plm:eco:{eco_no}"] if r else [])


@tool("maker")
def lot_change(ctx: Ctx, lot: str) -> Result:
    """The engineering change that put this material lot into use (same material, supplier and effectivity date), with its route and waiver status."""
    d = ctx.src.lot_change(lot)
    if d is None:
        return Result({"lot": lot, "error": "unknown lot"}, [])
    return Result(d, [f"mes:lot:{lot}"] + ([f"plm:eco:{d['eco_no']}"] if d.get("eco_no") else []))


@tool("maker")
def test_records(ctx: Ctx, serial: str) -> Result:
    """Factory test records for a serial (press-fit, run-in, hydro...)."""
    return Result({"serial": serial, "tests": ctx.src.test_records(serial)}, [f"mes:tests:{serial}"])


@tool("maker")
def lot_tests(ctx: Ctx, lot: str, test_kind: str = "press_fit_force") -> Result:
    """Average of a factory test across all units built with a lot, against units built with other lots of the same material."""
    d = ctx.src.lot_tests(lot, test_kind)
    if d is None:
        return Result({"lot": lot, "error": "unknown lot"}, [])
    d["deficit_pct"] = round((1 - d["lot_avg"] / d["other_avg"]) * 100, 1) if d["lot_n"] and d["other_n"] and d["other_avg"] else None
    return Result(d, [f"mes:lot_tests:{lot}:{test_kind}"])


@tool("maker")
def warranty_claims(ctx: Ctx, serial: str | None = None) -> Result:
    """Warranty claims on file (optionally for one serial)."""
    return Result({"claims": ctx.src.claims(serial)}, [f"qms:claims:{serial or 'all'}"])


@tool("maker")
def difa(ctx: Ctx, well: str | None = None, seal_built_since: str | None = None) -> Result:
    """Dismantle inspection and failure analysis (DIFA) reports, optionally for one well."""
    rows = ctx.src.difa(well, ctx.today.isoformat())
    sw = [r for r in rows if "elastomers swollen" in r["finding"]]
    return Result({"reports": len(rows), "elastomer_findings": len(sw), "items": [{"difa": r["difa_no"], "string": r["string_serial"], "well": r["well"], "date": r["report_date"], "finding": r["finding"]} for r in rows]},
                  [f"difa:{r['difa_no']}" for r in rows])


# =============================================================== drafts (writes are drafts, never executed) and OT (never written)
@tool("drafts", access="draft")
def create_draft(ctx: Ctx, kind: str, title: str, payload: dict, rationale: str, evidence: list[str]) -> Result:
    """Create a DRAFT in a target system. Nothing is sent: a named person in the approver role must approve it first."""
    if kind not in APPROVER_ROLES:
        return Result(None, refused=f"unknown draft kind {kind}")
    d = STORE.create(kind, title, payload, rationale, evidence, case_clock=ctx.as_of)
    return Result({"draft_id": d.id, "kind": kind, "status": d.status, "approver_role": d.approver_role}, [f"draft:{d.id}"])


@tool("ot", access="ot_write")
def write_setpoint(ctx: Ctx, tag: str, value: float) -> Result:
    """Write a value to an OT system (DCS/SCADA/VSD). Agents are never allowed to; this tool only records the refusal."""
    return Result({"tag": tag, "value": value}, [f"ot:write_refused:{tag}"], refused="OT is read-only for agents. Set-point changes are made by the control-room operator under the site's management-of-change process; "
                                                         "I can draft a request for the operator to review instead.")
