"""Build the instance knowledge graph from the source-system files.

Reads only what the systems hold (never truth.json). Every identity link carries a method and a
confidence; links below AUTO_ACCEPT go to the review queue instead of the graph.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from .rdfutil import FTF, Builder, iri

AUTO_ACCEPT = 0.90
WORLD = {"SAP-PM": "IT", "PI": "OT", "SCADA": "OT", "P&ID": "ET", "EDMS": "ET", "OSDU": "ET", "MES": "OT", "ERP": "IT",
         "QMS": "IT", "PLM": "ET", "RELIABILITY": "IT", "PRODUCTION": "IT"}
ASOF = date(2026, 10, 17)
SERIAL_RE = re.compile(r"^(OEM|ES|SS|PM|IN|MT|CB)-(\d\d)-(\d{1,4})$")


def d(s: str | None) -> date | None:
    if not s or s.startswith("9999"):
        return None
    return date.fromisoformat(s[:10])


def norm_serial(s: str | None) -> str:
    if not s:
        return ""
    t = re.sub(r"[\s_]+", "-", s.strip().upper())
    t = re.sub(r"^0EM", "OEM", t)
    m = SERIAL_RE.match(t)
    return f"{m.group(1)}-{m.group(2)}-{int(m.group(3)):04d}" if m else t


def lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


@dataclass
class Link:
    system: str
    table: str
    key: str
    canon: str
    method: str
    conf: float
    evidence: str


@dataclass
class Result:
    builder: Builder
    links: list[Link] = field(default_factory=list)
    review: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def _rows(con: sqlite3.Connection, sql: str, *a) -> list[sqlite3.Row]:
    con.row_factory = sqlite3.Row
    return con.execute(sql, a).fetchall()


class Pipeline:
    def __init__(self, src: Path, decisions: dict[str, str] | None = None) -> None:
        self.src = src
        self.b = Builder()
        self.links: list[Link] = []
        self.review: list[dict] = []
        self.decisions = decisions or {}  # "system|table|key" -> canon, from the review queue
        self.pos_by_tag: dict[str, str] = {}
        self.pos_by_floc: dict[str, str] = {}
        self.unit_by_equnr: dict[int, str] = {}
        self.unit_serials: dict[str, str] = {}
        self.installs: dict[str, list[tuple[date, date | None, str, str]]] = defaultdict(list)  # pos -> (from, to_excl, unit, inst canon)
        self.org: dict[str, str] = {}

    # ---------------------------------------------------------------- helpers
    def link(self, system: str, table: str, key: str, canon: str, method: str, conf: float, evidence: str, obj=None) -> bool:
        k = f"{system}|{table}|{key}"
        if k in self.decisions:
            canon, method, conf, evidence = self.decisions[k], "human", 1.0, "confirmed in review queue"
        if conf < AUTO_ACCEPT:
            self.review.append({"id": k, "system": system, "table": table, "key": key, "candidate": canon, "method": method,
                                "confidence": round(conf, 3), "evidence": evidence, "status": "open"})
            return False
        self.links.append(Link(system, table, key, canon, method, conf, evidence))
        if method not in ("exact_key",) and obj is not None:
            self.b.assertion(obj, f"{system}.{table}", iri(canon), method, conf, evidence)
        return True

    def db(self, name: str) -> sqlite3.Connection:
        return sqlite3.connect(self.src / name)

    def org_id(self, name: str, kind: str = "operator") -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        cid = f"org:{slug}"
        if cid not in self.org:
            self.org[cid] = name
            self.b.node(cid, "Organization", name, org_kind=kind)
        return cid

    # ---------------------------------------------------------------- stages
    def sites_and_positions(self) -> None:
        sap = self.db("sap_pm.sqlite")
        for r in _rows(sap, "SELECT * FROM T001W"):
            self.b.node(f"site:{r['werks']}", "Site", r["name"], site_kind=r["kind"], time_zone=r["tz"])
            self.org_id("Aurelia Energy")
        for r in _rows(sap, "SELECT * FROM IFLOT ORDER BY tplnr"):
            fl, plant = r["tplnr"], r["swerk"]
            m = re.match(r"^FA-P(\d)-([AB])(\d\d)(-ESP)?$", fl)
            if m:
                tag = f"{m.group(2)}-{m.group(3)}" + ("-ESP" if m.group(4) else "")
                if m.group(4):
                    cls = "ESPPosition"
                else:
                    cls = "Well"
            else:
                tag = fl.split("-", 1)[1]
                cls = "PumpPosition" if r["eqart"] == "PUMP" else "FunctionalLocation"
            canon = f"pos:{plant}:{tag}"
            self.pos_by_floc[fl] = canon
            self.pos_by_tag[tag] = canon
            u = self.b.node(canon, cls, r["pltxt"], site=iri(f"site:{plant}"), function=r["pltxt"].split(" ", 1)[-1])
            if cls == "Well":
                self.b.set(u, "pad", f"P{m.group(1)}")
                self.b.set(u, "lift_method", "esp" if tag.startswith("A-") else "gas_lift")
            self.b.ident(u, "SAP-PM", "IT", "floc", fl)
            self.link("SAP-PM", "IFLOT", fl, canon, "exact_key", 1.0, "functional location is the position backbone")
        for r in _rows(sap, "SELECT tplnr, tplma FROM IFLOT WHERE tplma IS NOT NULL"):
            self.b.set(iri(self.pos_by_floc[r["tplnr"]]), "parent", iri(self.pos_by_floc[r["tplma"]]))
        # installed spare: B is the installed spare of A
        for tag, canon in list(self.pos_by_tag.items()):
            if re.match(r"^\d\d-P-\d{3}B$", tag):
                self.b.set(iri(canon), "installed_spare_of", iri(self.pos_by_tag[tag[:-1] + "A"]))

    def engineering(self) -> None:
        pid = json.loads((self.src / "pid_dexpi.json").read_text())
        self.instrument_pumps: dict[str, list[str]] = {}
        for dr in pid["Drawings"]:
            doc = f"doc:{dr['Drawing']}"
            self.b.node(doc, "Document", f"P&ID {dr['Drawing']}", doc_kind="P&ID", revision=dr["Revision"])
            for it in dr["PlantItems"]:
                if it["ComponentClass"] == "CentrifugalPump":
                    canon = self.pos_by_tag.get(it["TagName"])
                    if canon is None:
                        continue
                    self.link("P&ID", "PlantItem", it["TagName"], canon, "exact_key", 1.0, "P&ID tag equals the tag part of the functional location")
                    self.b.set(iri(doc), "depicts", iri(canon))
                    self.b.ident(iri(canon), "P&ID", "ET", "tag", it["TagName"])
                elif it.get("ConnectedTo"):
                    self.instrument_pumps[it["TagName"]] = [self.pos_by_tag[t] for t in it["ConnectedTo"] if t in self.pos_by_tag]
        with open(self.src / "edms_documents.csv") as f:
            for r in csv.DictReader(f):
                canon = f"doc:{r['doc_no']}"
                dep = []
                for t in r["applies_to"].split(";"):
                    p = self.pos_by_tag.get(t)
                    if p is None and re.match(r"^A-\d\d$", t):
                        p = self.pos_by_tag.get(t)
                        esp = self.pos_by_tag.get(t + "-ESP")
                        if esp and r["kind"] in ("completion schematic",):
                            dep.append(iri(esp))
                    if p:
                        dep.append(iri(p))
                        self.link("EDMS", "doc_applies", f"{r['doc_no']}|{t}", p, "exact_key", 1.0, "tag listed in the document register")
                        if esp_sibling := self.pos_by_tag.get(t + "-ESP"):
                            self.link("EDMS", "doc_applies", f"{r['doc_no']}|{t}", esp_sibling, "exact_key", 1.0, "ESP position of that well") if r["kind"] == "completion schematic" else None
                    else:
                        pass
                self.b.node(canon, "Document", r["title"], doc_kind=r["kind"], revision=r["revision"], depicts=dep)
        wells = json.loads((self.src / "osdu_wells.json").read_text())["results"]
        for wl in wells:
            m = re.search(r"FA-([AB])(\d\d)$", wl["WellID"])
            tag = f"{m.group(1)}-{m.group(2)}"
            canon = self.pos_by_tag[tag]
            self.link("OSDU", "Well", wl["WellID"], canon, "tag_rule", 0.97, "OSDU well id suffix names the well", obj=iri(canon))
            self.b.ident(iri(canon), "OSDU", "ET", "well_id", wl["WellID"])

    def units(self) -> None:
        sap, mes, erp = self.db("sap_pm.sqlite"), self.db("kestrel_mes.sqlite"), self.db("kestrel_erp.sqlite")
        builds = {r["serial"]: r for r in _rows(mes, "SELECT * FROM build_records")}
        ships = defaultdict(list)
        cust = {r["customer_no"]: r["name"] for r in _rows(erp, "SELECT * FROM customers")}
        for r in _rows(erp, "SELECT * FROM shipments"):
            ships[r["serial_no"]].append(r)
        ship_by_key: dict[tuple, list[str]] = defaultdict(list)
        for s, lst in ships.items():
            for r in lst:
                if cust[r["customer_no"]] == "Aurelia Energy":
                    ship_by_key[(builds[s]["model"], r["ship_date"])].append(s)
        # components from the maker's assembly table
        parent_of = {r["component_serial"]: r["parent_serial"] for r in _rows(mes, "SELECT * FROM assembly")}
        matched_mes: dict[str, int] = {}
        # --- SAP equipment -> maker serial
        sap_units: dict[int, str] = {}
        deferred: list = []
        children = defaultdict(list)
        for comp, par in parent_of.items():
            children[par].append(comp)

        def settle(eq: int, canon: str | None, m: str, c: float, ev: str, raw: str) -> None:
            if canon is None:
                n = norm_serial(raw)
                ucanon = f"unit:{n}" if n else f"unit:SAP-{eq}"
                m, c, ev = "exact_key", 1.0, "no maker record in this graph; keyed by CMMS serial"
            else:
                ucanon = f"unit:{canon}"
                matched_mes[canon] = eq
            sap_units[eq] = ucanon
            self.unit_by_equnr[eq] = ucanon
            self.link("SAP-PM", "EQUI", str(eq), ucanon, m if canon else "exact_key", c, ev)

        for r in _rows(sap, "SELECT * FROM EQUI ORDER BY equnr"):
            raw, eq = r["sernr"] or "", r["equnr"]
            canon = None
            m = c = ev = None
            if r["herst"] == "Kestrel Pump Works":
                if raw in builds:
                    canon, m, c, ev = raw, "exact_key", 1.0, "serial identical in CMMS and maker MES"
                elif norm_serial(raw) in builds:
                    canon, m, c, ev = norm_serial(raw), "exact_key", 0.97, f"serial normalised from '{raw}'"
                elif raw:
                    cand = [s for s in builds if lev(norm_serial(raw), s) <= 1]
                    if len(cand) == 1:
                        canon, m, c, ev = cand[0], "fuzzy", 0.92, f"edit distance 1 from '{raw}'"
                else:
                    ym = (r["baujj"], r["baumm"])
                    pool = [s for s in ship_by_key.get((r["typbz"], r["ansdt"]), [])
                            if (int(builds[s]["built"][:4]), int(builds[s]["built"][5:7])) == ym and s not in matched_mes]
                    if len(pool) == 1:
                        canon, m, c, ev = pool[0], "fuzzy", 0.93, "blank serial; model, build month and goods-receipt date match one shipment"
                    else:
                        deferred.append(r)
                        continue
            settle(eq, canon, m, c, ev, raw)
        for r in deferred:
            eq = r["equnr"]
            par_unit = self.unit_by_equnr.get(r["hequi"]) if r["hequi"] else None
            pool = []
            if par_unit and par_unit.startswith("unit:"):
                pool = [s for s in children.get(par_unit[5:], []) if builds[s]["model"] == r["typbz"] and s not in matched_mes]
            if len(pool) == 1:
                settle(eq, pool[0], "fuzzy", 0.93, "blank serial; the only component of that model in the parent assembly", "")
            else:
                self.review.append({"id": f"SAP-PM|EQUI|{eq}", "system": "SAP-PM", "table": "EQUI", "key": str(eq), "candidate": None,
                                    "method": "fuzzy", "confidence": 0.0, "evidence": f"blank serial; {len(pool)} candidates", "status": "open"})
                settle(eq, None, "exact_key", 1.0, "", "")
        # --- build every unit node (CMMS side, then maker-only units)
        kind_of = {"PM": "pump", "IN": "intake", "MT": "motor", "CB": "cable"}
        def cls_for(model: str) -> tuple[str, str | None]:
            if model.startswith("KE-ESP"):
                return "ESPString", None
            if model.startswith("KE-SEAL"):
                return "ESPComponent", "seal_section"
            mm = re.match(r"KE-(PM|IN|MT|CB)-", model)
            if mm:
                return "ESPComponent", kind_of[mm.group(1)]
            return "PhysicalEquipment", None
        made: set[str] = set()
        for r in _rows(sap, "SELECT * FROM EQUI"):
            ucanon = sap_units[r["equnr"]]
            raw = r["sernr"] or ""
            serial = ucanon.split(":", 1)[1] if not ucanon.startswith("unit:SAP-") else (r["sernr"] or f"SAP-{r['equnr']}")
            b = builds.get(serial)
            built = d(b["built"]) if b else date(r["baujj"], r["baumm"], 1)
            model = b["model"] if b else r["typbz"]
            cls, ck = cls_for(model)
            maker = self.org_id(r["herst"], "oem" if r["herst"] else "supplier")
            u = self.b.node(ucanon, cls, serial, serial=serial, model=model, manufacturer=iri(maker), built_on=built, kind=ck)
            self.b.ident(u, "SAP-PM", "IT", "equipment_no", str(r["equnr"]))
            if raw and raw != serial:
                self.b.ident(u, "SAP-PM", "IT", "serial_as_typed", raw)
            if b:
                self.b.ident(u, "MES", "OT", "serial", serial)
                self.link("MES", "build_records", serial, ucanon, "exact_key", 1.0, "maker serial")
            made.add(ucanon)
            self.unit_serials[ucanon] = serial
        for s, b in builds.items():
            ucanon = f"unit:{s}"
            if ucanon in made:
                continue
            cls, ck = cls_for(b["model"])
            u = self.b.node(ucanon, cls, s, serial=s, model=b["model"], manufacturer=iri(self.org_id("Kestrel Pump Works", "oem")),
                            built_on=d(b["built"]), kind=ck)
            self.b.ident(u, "MES", "OT", "serial", s)
            self.link("MES", "build_records", s, ucanon, "exact_key", 1.0, "maker serial")
            self.unit_serials[ucanon] = s
        # superior equipment: maker assembly is authoritative; CMMS hequi is a cross-check
        for comp, par in parent_of.items():
            if f"unit:{comp}" in self.b.nodes and f"unit:{par}" in self.b.nodes:
                self.b.set(iri(f"unit:{comp}"), "parent_unit", iri(f"unit:{par}"))
        for strn in [u for u, c in self.b.nodes.items() if c == "ESPString"]:
            comps = [iri(c) for c in self.b.nodes if self.b.nodes[c] == "ESPComponent" and (iri(c), FTF["parent_unit"], iri(strn)) in self.b.g]
            self.b.set(iri(strn), "components", comps)
        # --- genealogy, lots, shipments, tests
        self.lots_from_maker(mes, erp)
        for s, lst in ships.items():
            for r in lst:
                cname = cust[r["customer_no"]]
                oc = self.org_id(cname)
                sid = f"ship:{r['delivery_no']}:{s}"
                self.b.node(sid, "Shipment", f"{s} to {cname}", unit=iri(f"unit:{s}"), customer=iri(oc), shipped_on=d(r["ship_date"]))
                self.b.set(iri(f"unit:{s}"), "owner_org", None)
                self.link("ERP", "shipments", f"{r['delivery_no']}|{s}", f"unit:{s}", "exact_key", 1.0, "shipment line carries the maker serial")
        for r in _rows(mes, "SELECT * FROM test_records"):
            tid = f"test:{r['serial']}:{r['test_kind']}"
            self.b.node(tid, "TestRecord", f"{r['test_kind']} {r['serial']}", unit=iri(f"unit:{r['serial']}"), test_kind=r["test_kind"],
                        passed=bool(r["passed"]), value=float(r["value"]), engineering_unit=r["unit"], occurred_on=None)
        for s, b in builds.items():
            self.b.node(f"build:{s}", "BuildRecord", f"Build {s}", unit=iri(f"unit:{s}"), built_on=d(b["built"]), work_order=b["work_order"])
        # --- installations (time segments)
        for r in _rows(sap, "SELECT * FROM EQUZ ORDER BY tplnr, datab"):
            pos = self.pos_by_floc.get(r["tplnr"])
            unit = self.unit_by_equnr.get(r["equnr"])
            if not pos or not unit:
                continue
            frm = d(r["datab"])
            end_incl = d(r["datbi"])
            to = end_incl + timedelta(days=1) if end_incl else None
            ic = f"inst:{pos.split(':', 1)[1]}:{unit.split(':', 1)[1]}:{frm}"
            self.b.node(ic, "Installation", f"{unit.split(':', 1)[1]} at {pos.split(':')[-1]} from {frm}", position=iri(pos), unit=iri(unit), from_date=frm, to_date=to)
            self.installs[pos].append((frm, to, unit, ic))
        for lst in self.installs.values():
            lst.sort(key=lambda x: x[0])

    def lots_from_maker(self, mes, erp) -> None:
        plm = self.db("kestrel_plm.sqlite")
        sup = {r["supplier_code"]: r["name"] for r in _rows(erp, "SELECT * FROM suppliers")}
        ecos = {}
        for r in _rows(plm, "SELECT * FROM eco"):
            ecos[r["eco_no"]] = r
            self.b.node(f"eco:{r['eco_no']}", "EngineeringChange", r["title"], approved_on=d(r["approved"]), route=r["route"].lower(),
                        qualification_test_waived=(r["qualification_test_waived"] == "Y"), change_summary=r["summary"])
            self.link("PLM", "eco", r["eco_no"], f"eco:{r['eco_no']}", "exact_key", 1.0, "ECO number")
        eff = list(_rows(plm, "SELECT * FROM eco_effectivity"))
        lots = {}
        for r in _rows(mes, "SELECT * FROM lots"):
            lc = f"lot:{r['lot_id']}"
            lots[r["lot_id"]] = r
            so = self.org_id(sup[r["supplier_code"]], "supplier")
            u = self.b.node(lc, "MaterialLot", r["lot_id"], material=r["material"], supplier=iri(so))
            self.link("MES", "lots", r["lot_id"], lc, "exact_key", 1.0, "lot id")
            # lot -> ECO: same part, same supplier, received on or after the effectivity date; latest wins
            cands = [e for e in eff if e["part"] == r["material"] and e["supplier_code"] == r["supplier_code"] and r["received"] >= e["effective_from"]]
            if cands:
                e = max(cands, key=lambda x: x["effective_from"])
                self.b.set(u, "introduced_by", iri(f"eco:{e['eco_no']}"))
                self.links.append(Link("PLM", "lot_eco", r["lot_id"], f"eco:{e['eco_no']}", "effectivity_rule", 0.95,
                                       f"part '{r['material']}' from supplier {r['supplier_code']} received {r['received']} after effectivity {e['effective_from']}"))
                self.b.assertion(u, "ftf:introduced_by", iri(f"eco:{e['eco_no']}"), "tag_rule", 0.95, "ECO effectivity (part + supplier + date)")
        gen = defaultdict(list)
        for r in _rows(mes, "SELECT * FROM genealogy WHERE lot_id <> '-'"):
            gen[r["serial"]].append(iri(f"lot:{r['lot_id']}"))
        for s, ls in gen.items():
            if f"unit:{s}" in self.b.nodes:
                self.b.set(iri(f"unit:{s}"), "build_lots", ls)

    def signals(self) -> None:
        pi, sc, _sap = self.db("historian_pi.sqlite"), self.db("scada_fielda.sqlite"), self.db("sap_pm.sqlite")
        floc_by_prefix = defaultdict(dict)
        for fl, canon in self.pos_by_floc.items():
            if "-P-" in fl:
                prefix, rest = fl.split("-", 1)
                floc_by_prefix[prefix][rest.split("-", 1)[1]] = canon  # "P-101A" -> pos
        qty = {"VIB_DE": ("vibration_de", "Drive-end bearing vibration"), "VIB_NDE": ("vibration_nde", "Non-drive-end bearing vibration"),
               "BRG_T": ("bearing_temp", "Bearing temperature"), "RUN": ("run_status", "Run status")}
        self.signal_count = 0
        for r in _rows(pi, "SELECT * FROM tags ORDER BY tag_id"):
            name, desc, asset = r["name"], r["descriptor"] or "", r["asset_path"]
            pos, method, conf, ev = None, None, 0.0, ""
            canon_name = name
            alias = pi.execute("SELECT current_name FROM tag_alias WHERE legacy_name=?", (name,)).fetchone()
            if alias:
                canon_name, method, conf, ev = alias[0], "alias_table", 1.0, f"retired tag {name}, renamed {alias[0]} on migration"
            m = re.match(r"^(\d\d)P(\d{3})([AB])[._](VIB_DE|VIB_NDE|BRG_T|RUN)$", canon_name)
            sfx = None
            if m:
                tag = f"{m.group(1)}-P-{m.group(2)}{m.group(3)}"
                pos, sfx = self.pos_by_tag.get(tag), m.group(4)
                if pos and not alias:
                    method, conf, ev = "tag_rule", 0.98, f"tag grammar AAPNNNL.SUFFIX -> {tag}"
            mi = re.match(r"^(\d\d)PI(\d{4})\.PV$", canon_name)
            multi: list[str] = []
            if mi:
                multi = self.instrument_pumps.get(f"{mi.group(1)}-PI-{mi.group(2)}", [])
                if multi:
                    method, conf, ev = "tag_rule", 0.95, f"P&ID instrument {mi.group(1)}-PI-{mi.group(2)} is connected to {', '.join(t.split(':')[-1] for t in multi)}"
            if pos is None and not multi:
                # no usable tag grammar: fall back to the asset-framework path, then the descriptor text
                if asset:
                    mp = re.match(r"^\\\\(\w+)\\(P-\d{3}[AB])$", asset)
                    if mp:
                        pos = floc_by_prefix.get(mp.group(1), {}).get(mp.group(2))
                        if pos:
                            method, conf, ev = "alias_table", 0.95, f"asset-framework path {asset}"
                if pos is None:
                    md = re.search(r"\b(\d\d-P-\d{3}[AB])\b", desc)
                    if md and md.group(1) in self.pos_by_tag:
                        pos, method, conf, ev = self.pos_by_tag[md.group(1)], "fuzzy", 0.92, f"descriptor names {md.group(1)}"
                    ms = re.search(r"(VIB_DE|VIB_NDE|BRG_T|RUN)$", canon_name)
                    sfx = ms.group(1) if ms else None
                if pos and sfx is None:
                    ms = re.search(r"(VIB_DE|VIB_NDE|BRG_T|RUN)$", name.replace(".", "_"))
                    sfx = ms.group(1) if ms else None
            if sfx and sfx in qty:
                quantity = qty[sfx][0]
            elif mi:
                quantity = "suction_pressure"
            else:
                quantity = "unknown"
            targets = [pos] if pos else multi
            sc_ = f"sig:{name}"
            u = self.b.node(sc_, "Signal", f"{name} {desc}".strip(), quantity=quantity, engineering_unit=r["engunits"], alarm_high=r["alarm_high"],
                            sample_seconds=r["sample_s"])
            self.b.ident(u, "PI", "OT", "tag", name)
            self.signal_count += 1
            if targets:
                for t in targets:
                    if self.link("PI", "tags", name, t, method, conf, ev, obj=iri(sc_)):
                        self.b.set(u, "measures_position", iri(t))
            else:
                self.review.append({"id": f"PI|tags|{name}", "system": "PI", "table": "tags", "key": name, "candidate": None, "method": "fuzzy",
                                    "confidence": 0.0, "evidence": "no tag grammar, asset path or descriptor matched", "status": "open"})
            if r["retired"] and pos:
                pass
        for r in _rows(sc, "SELECT * FROM tags ORDER BY tag_id"):
            name = r["name"]
            m = re.match(r"^([AB])(\d\d)_(\w+)$", name)
            pos = None
            if m:
                well = f"{m.group(1)}-{m.group(2)}"
                is_esp = f"{well}-ESP" in self.pos_by_tag
                pos = self.pos_by_tag.get(f"{well}-ESP") if is_esp else self.pos_by_tag.get(well)
            sc_ = f"sig:{name}"
            quantity = {"MTR_T": "motor_temperature", "PIP": "intake_pressure", "AMPS": "motor_current", "VSD_HZ": "drive_frequency",
                        "LEAK_I": "leakage_current", "FLOW": "flow", "THP": "tubing_head_pressure", "GL_FLOW": "gas_lift_rate"}.get(m.group(3) if m else "", "unknown")
            u = self.b.node(sc_, "Signal", f"{name} {r['descriptor']}", quantity=quantity, engineering_unit=r["engunits"], alarm_high=r["alarm_high"], sample_seconds=r["sample_s"])
            self.b.ident(u, "SCADA", "OT", "tag", name)
            self.signal_count += 1
            if pos and self.link("SCADA", "tags", name, pos, "tag_rule", 0.97, f"tag grammar {m.group(1)}NN_* names well {well}", obj=iri(sc_)):
                self.b.set(u, "measures_position", iri(pos))
                self.b.ident(iri(pos), "SCADA", "OT", "tag_prefix", f"{m.group(1)}{m.group(2)}_")

    def events(self) -> None:
        sap = self.db("sap_pm.sqlite")
        codes = {}
        with open(self.src / "failure_code_map.csv") as f:
            for r in csv.DictReader(f):
                codes[r["sap_code"]] = r["iso14224_mode"]
        n_failures = 0
        for r in _rows(sap, "SELECT * FROM QMEL ORDER BY qmdat, qmnum"):
            pos = self.pos_by_floc.get(r["tplnr"])
            on = d(r["qmdat"])
            unit = self.unit_by_equnr.get(r["equnr"]) if r["equnr"] else None
            how = "equipment number on the notification"
            conf = 1.0
            if unit is None and pos:
                for frm, to, u, ic in self.installs.get(pos, []):
                    if frm <= on and (to is None or on < to):
                        unit, how, conf = u, "installation at the position on the notification date", 0.95
                        break
            nc = f"nt:{r['qmnum']}"
            if pos:
                self.link("SAP-PM", "QMEL", r["qmnum"], pos, "exact_key", 1.0, "functional location on the notification")
            if unit:
                self.link("SAP-PM", "QMEL_unit", r["qmnum"], unit, "exact_key" if conf == 1.0 else "tag_rule", conf, how)
            self.b.node(nc, "Notification", r["qmtxt"], occurred_on=on, about_position=iri(pos) if pos else None,
                        about_unit=iri(unit) if unit else None, text=(r["qmtxt"] + (" | " + r["ltxt"] if r["ltxt"] else "")))
            if r["qmart"] != "M2" or not pos:
                continue
            mode = codes.get(r["fecod"] or "")
            mconf, mhow = 1.0, "governed failure-code map"
            if mode is None:
                t = (r["qmtxt"] or "").lower()
                mode = "VIB" if "vib" in t else "ELP" if "leak" in t else None
                mconf, mhow = 0.92, "legacy code; mode read from the notification text"
            if mode is None or unit is None:
                continue
            inst = next((ic for frm, to, u, ic in self.installs.get(pos, []) if u == unit and frm <= on and (to is None or on < to)), None)
            self.b.node(f"fe:{r['qmnum']}", "FailureEvent", f"{mode} {unit.split(':', 1)[1]} {on}", occurred_on=on, mode=mode, of_unit=iri(unit),
                        at_position=iri(pos), installation=iri(inst) if inst else None, description=r["qmtxt"])
            n_failures += 1
            if conf < 1.0:
                self.b.assertion(iri(f"fe:{r['qmnum']}"), "ftf:of_unit", iri(unit), "tag_rule", conf, how)
            if mconf < 1.0:
                self.b.assertion(iri(f"fe:{r['qmnum']}"), "ftf:mode", iri(f"enum:{mode}"), "tag_rule", mconf, mhow)
        self.n_failures = n_failures

    def reliability(self) -> None:
        with open(self.src / "reliability_runlife.csv") as f:
            for r in csv.DictReader(f):
                tag = f"{r['well']}-ESP"
                pos = self.pos_by_tag.get(tag)
                unit = f"unit:{norm_serial(r['string_serial'])}"
                if not pos or unit not in self.b.nodes:
                    continue
                self.link("RELIABILITY", "runlife", f"{r['well']}|{r['string_serial']}", pos, "tag_rule", 0.95,
                               f"run-life tool is keyed by well name {r['well']}; the ESP position is its child", obj=iri(unit))
                start, end = d(r["set_date"]), d(r["pull_date"])
                inst = next((ic for frm, to, u, ic in self.installs.get(pos, []) if u == unit and frm == start), None)
                if inst is None:
                    # the CMMS lost this time segment; the run-life tool is a second witness for it
                    inst = f"inst:{pos.split(':', 1)[1]}:{unit.split(':', 1)[1]}:{start}"
                    self.b.node(inst, "Installation", f"{unit.split(':', 1)[1]} at {pos.split(':')[-1]} from {start}", position=iri(pos), unit=iri(unit),
                                from_date=start, to_date=end)
                    self.installs[pos].append((start, end, unit, inst))
                    self.b.assertion(iri(inst), "ftf:unit", iri(unit), "tag_rule", 0.95, "installation recovered from the run-life record")
                rid = f"run:{r['well']}:{r['string_serial']}:{start}"
                self.b.node(rid, "RunRecord", f"{r['string_serial']} in {r['well']} from {start}", installation=iri(inst) if inst else None, start=start, end=end,
                            end_state="failed" if end else "running", run_days=((end or ASOF) - start).days)
        with open(self.src / "difa_reports.csv") as f:
            for r in csv.DictReader(f):
                unit = f"unit:{norm_serial(r['string_serial'])}"
                if unit in self.b.nodes:
                    self.b.node(f"doc:{r['difa_no']}", "Document", f"{r['difa_no']} {r['string_serial']}", doc_kind="DIFA report", about_unit=iri(unit),
                                summary=r["finding"], issued_on=d(r["report_date"]))
        qms = self.db("kestrel_qms.sqlite")
        cust = {r["customer_no"]: r["name"] for r in _rows(self.db("kestrel_erp.sqlite"), "SELECT * FROM customers")}
        for r in _rows(qms, "SELECT * FROM warranty_claims"):
            units = [iri(f"unit:{x['serial_no']}") for x in _rows(qms, "SELECT serial_no FROM claim_units WHERE claim_no=?", r["claim_no"])]
            self.b.node(f"claim:{r['claim_no']}", "WarrantyClaim", f"{r['claim_no']} {r['status']}", raised_by=iri(self.org_id(cust[r["customer_no"]])),
                        covers_units=units, opened_on=d(r["opened"]))

    def kpis(self) -> None:
        for k, q, g, m, s, qf in (
            ("kpi:mtbf", "How long does a unit run between failures?", "unit", "Operating days divided by failure count, counted per unit, not per position", "ISO 14224", "cq03"),
            ("kpi:run_life_km", "How long do strings built with a given material last?", "lot", "Kaplan-Meier median run life; running strings are censored", "API RP 11S1", "cq07"),
            ("kpi:elp_rate", "How often does a unit leak at the seal?", "unit", "External leakage (process) failures per unit-year", "ISO 14224", "cq02"),
            ("kpi:deferment", "How much oil is at risk while a well runs degraded?", "position", "Allocated oil rate lost against the pre-event rate", None, "cq08")):
            self.b.node(k, "KpiDefinition", k.split(":")[1], question=q, grain=g, method=m, standard=s, query=qf)

    def build(self) -> Result:
        self.sites_and_positions()
        self.engineering()
        self.units()
        self.signals()
        self.events()
        self.reliability()
        self.kpis()
        res = Result(self.b, self.links, self.review)
        res.stats = {"triples": len(self.b.g), "nodes": len(self.b.nodes), "links": len(self.links), "review_open": len(self.review),
                     "failures": self.n_failures, "signals": self.signal_count}
        return res
