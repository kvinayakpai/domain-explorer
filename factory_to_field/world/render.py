"""Render the one true world into the files each source system would hold.

The renderers add what real systems add: different names for the same thing, local times in one place
and UTC in another, retired tag names, mixed engineering units, typos, blank fields, free text.
Nothing here leaks the canonical ids; those go only to truth.json for scoring.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from .model import World
from .signals import DATES, N, alarms, drive_events
from .spec import HIST_START, NOW, ORGS

SAP_CODE = {"VIB": "VB01", "ELP": "LK02", "ELU": "LK03", "OHE": "TH03", "NOI": "NS04", "PDE": "PD05", "BRD": "BR06", "FTS": "ST07",
            "STP": "TR08", "INL": "LK09", "ERO": "ER10", "SER": "SV11"}
R2_MIGRATION = date(2025, 9, 12)
FIXED_EQUNR = {"OEM-24-0412": 10003977, "OEM-25-1187": 10004512, "ES-25-0233": 20009154, "ES-23-0117": 20007781}
MESSY = {"OEM-24-0398": "OEM 24 0398", "OEM-25-1150": "0EM-25-1150"}


class Truth:
    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str, str]] = []

    def add(self, system: str, table: str, key: str, canon: str) -> None:
        self.rows.append((system, table, str(key), canon))


def _db(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    return sqlite3.connect(path)


def _mess(w: World, serial: str, maker_is_kestrel: bool) -> str:
    if serial in MESSY:
        return MESSY[serial]
    if not maker_is_kestrel:
        return serial
    r = w.rng.random()
    if r < 0.012:
        return serial.lower()
    if r < 0.024:
        return serial.replace("-", " ")
    if r < 0.032:
        return serial.replace("OEM", "0EM")
    if r < 0.040:
        a, b, c = serial.split("-")
        return f"{a}-{b}-{int(c)}"
    if r < 0.050:
        return ""  # blank in the CMMS
    return serial


def render_sap(w: World, out: Path, tr: Truth) -> None:
    con = _db(out / "sap_pm.sqlite")
    con.executescript("""
    CREATE TABLE IFLOT(tplnr TEXT PRIMARY KEY, pltxt TEXT, tplma TEXT, swerk TEXT, eqart TEXT, fltyp TEXT);
    CREATE TABLE EQUI(equnr INTEGER PRIMARY KEY, sernr TEXT, herst TEXT, typbz TEXT, baujj INTEGER, baumm INTEGER, hequi INTEGER, eqtyp TEXT, ansdt TEXT);
    CREATE TABLE EQUZ(equnr INTEGER, tplnr TEXT, datab TEXT, datbi TEXT);
    CREATE TABLE QMEL(qmnum TEXT PRIMARY KEY, qmart TEXT, qmtxt TEXT, ltxt TEXT, qmdat TEXT, mzeit TEXT, tplnr TEXT, equnr INTEGER, fecod TEXT, priok INTEGER, qmst TEXT);
    CREATE TABLE AUFK(aufnr TEXT PRIMARY KEY, auart TEXT, ktext TEXT, tplnr TEXT, equnr INTEGER, gstrp TEXT, gltrp TEXT, istat TEXT, qmnum TEXT);
    CREATE TABLE MARD(matnr TEXT, maktx TEXT, werks TEXT, lgort TEXT, labst INTEGER, wzeit INTEGER);
    CREATE TABLE T001W(werks TEXT PRIMARY KEY, name TEXT, tz TEXT, kind TEXT);
    CREATE TABLE MOC(moc TEXT, title TEXT, status TEXT, tplnr TEXT, opened TEXT);
    """)
    for pid, pos in w.positions.items():
        con.execute("INSERT INTO IFLOT VALUES(?,?,?,?,?,?)", (pos["floc"], f"{pos['tag']} {pos['service']}", None,
                                                              pos["site"].split(":")[1], "PUMP" if pos["kind"] == "pump" else pos["kind"].upper(), "PP"))
        tr.add("SAP-PM", "IFLOT", pos["floc"], pid)
    for pid, pos in w.positions.items():
        if pos.get("parent"):
            con.execute("UPDATE IFLOT SET tplma=? WHERE tplnr=?", (w.positions[pos["parent"]]["floc"], pos["floc"]))
    for sid, st in w.sites.items():
        if st['kind'] != 'factory':
            con.execute('INSERT INTO T001W VALUES(?,?,?,?)', (sid.split(':')[1], st['name'], st['tz'], st['kind']))
    # equipment
    equnr: dict[str, int] = {}
    nxt = {"10": 10000001, "20": 20000001}
    taken = set(FIXED_EQUNR.values())
    for uid, u in sorted(w.units.items()):
        if u["serial"] in FIXED_EQUNR:
            equnr[uid] = FIXED_EQUNR[u["serial"]]
            continue
        # units that belong to the operator are in its CMMS; other customers' units are not
        if u["customer"] != "cust:aurelia":
            continue
        if u["kind"].startswith("esp"):
            k = "20"
        else:
            k = "10"
        while nxt[k] in taken:
            nxt[k] += 1
        equnr[uid] = nxt[k]
        taken.add(nxt[k])
        nxt[k] += 1
    for uid, eq in equnr.items():
        u = w.units[uid]
        maker = ORGS[u["maker"]][0]
        ser = _mess(w, u["serial"], u["maker"] == "org:kestrel")
        parent = equnr.get(u["parent"]) if u.get("parent") else None
        b = u["built"]
        con.execute("INSERT INTO EQUI VALUES(?,?,?,?,?,?,?,?,?)", (eq, ser, maker, u["model"], b.year, b.month, parent,
                                                                     "M" if not u["kind"].startswith("esp") else "E", (u.get("shipped") or b).isoformat()))
        tr.add("SAP-PM", "EQUI", eq, uid)
    for inst in w.installs:
        if inst["unit"] not in equnr:
            continue
        # SAP keeps time segments; a few are never closed or recorded (data-quality realism, not on planted units)
        planted = w.units[inst["unit"]]["serial"] in {"OEM-24-0412", "OEM-25-1187", "OEM-21-0090", "ES-25-0233", "ES-23-0117"}
        if not planted and w.rng.random() < 0.02:
            continue
        con.execute("INSERT INTO EQUZ VALUES(?,?,?,?)", (equnr[inst["unit"]], w.positions[inst["pos"]]["floc"], inst["from"].isoformat(),
                                                         (inst["to"] - timedelta(days=1)).isoformat() if inst["to"] else "9999-12-31"))
    # notifications (local time at the site) and orders
    nq: dict[str, str] = {}
    for n in sorted(w.notifications, key=lambda x: (x["on"], x["id"])):
        pos = w.positions[n["pos"]]
        ZoneInfo(w.sites[pos["site"]]["tz"])
        hh, mm = int(w.rng.integers(5, 17)), int(w.rng.integers(0, 60))
        qm = f"{300000000 + len(nq) * 3 + 1}"
        nq[n["id"]] = qm
        code = SAP_CODE.get(n["mode"]) if n["mode"] else None
        if n["mode"] and w.rng.random() < 0.05:
            code = "VIBR" if n["mode"] == "VIB" else "LEAK"  # legacy local codes
        eq = equnr.get(n["unit"]) if n["unit"] else None
        con.execute("INSERT INTO QMEL VALUES(?,?,?,?,?,?,?,?,?,?,?)", (qm, n["type"], n["text"][:40], n.get("long") or None, n["on"].isoformat(),
                                                                         f"{hh:02d}:{mm:02d}:00", pos["floc"], eq, code, n["prio"], "NOCO" if n["status"] == "closed" else "OSNO"))
        tr.add("SAP-PM", "QMEL", qm, n["pos"])
        true_unit = next((f["unit"] for f in w.failures if f["id"] == n["fail"]), None) if n["fail"] else w.unit_at(n["pos"], n["on"])
        if true_unit:
            tr.add("SAP-PM", "QMEL_unit", qm, true_unit)
    for k_, o in enumerate(w.workorders):
        pos = w.positions[o["pos"]] if o["pos"] else None
        aufnr = f"{4000000 + k_}"
        tplnr = pos["floc"] if pos else None
        if pos is None and o.get("unit") and o["unit"] in equnr:
            w.installs_of(o["unit"])
            tplnr = None
        con.execute("INSERT INTO AUFK VALUES(?,?,?,?,?,?,?,?,?)", (aufnr, o["type"], o["text"][:40], tplnr, equnr.get(o["unit"]) if o.get("unit") else None,
                                                                   o["start"].isoformat(), o["end"].isoformat() if o["end"] else None,
                                                                   "REL" if o.get("open") else "TECO", nq.get(o["notif"]) if o.get("notif") else None))
    for s in w.stock:
        con.execute("INSERT INTO MARD VALUES(?,?,?,?,?,?)", (s["material"], s["desc"], s["site"].split(":")[1], s["store"], s["qty"], s["lead_days"]))
    for moc in (("MOC-2026-014", "Replace exchanger E-3012 tube bundle", "OPEN", "CDU2-30-E-3012", "2026-08-04"),
                ("MOC-2026-019", "Add vibration sensors on feed pumps", "CLOSED", "HTU1-21-P-212A", "2026-05-11"),
                ("MOC-2025-077", "Impeller trim for P-411A", "CLOSED", "FCC2-41-P-411A", "2025-11-02")):
        con.execute("INSERT INTO MOC VALUES(?,?,?,?,?)", moc)
    con.commit()
    con.close()
    w.answer["_equnr"] = {w.units[u]["serial"]: e for u, e in equnr.items()}
    with open(out / "failure_code_map.csv", "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["sap_code", "iso14224_mode", "description"])
        for k, v in SAP_CODE.items():
            cw.writerow([v, k, {"VIB": "Vibration", "ELP": "External leakage, process medium", "ELU": "External leakage, utility", "OHE": "Overheating",
                                "NOI": "Noise", "PDE": "Parameter deviation", "BRD": "Breakdown", "FTS": "Fail to start", "STP": "Spurious stop",
                                "INL": "Internal leakage", "ERO": "Erratic output", "SER": "Minor in-service problem"}[k]])


def _conv(w: World, sig: dict, arr: np.ndarray) -> np.ndarray:
    if sig["site"] == "site:R3" and sig["quantity"].startswith("vibration"):
        return arr / 25.4
    return arr


def _hist_db(w: World, out: Path, name: str, site_filter, tr: Truth, system: str) -> None:
    con = _db(out / name)
    con.executescript("""
    CREATE TABLE tags(tag_id INTEGER PRIMARY KEY, name TEXT, descriptor TEXT, engunits TEXT, pointsource TEXT, asset_path TEXT, alarm_high REAL, sample_s INTEGER, retired TEXT);
    CREATE TABLE daily(tag_id INTEGER, day TEXT, mean REAL, min REAL, max REAL, n_good INTEGER, n_bad INTEGER);
    CREATE TABLE raw(tag_id INTEGER, ts TEXT, value REAL, quality TEXT);
    CREATE TABLE alarms(tag_id INTEGER, ts TEXT, value REAL, limit_value REAL, state TEXT);
    CREATE TABLE tag_alias(legacy_name TEXT, current_name TEXT, migrated_on TEXT);
    CREATE INDEX ix_daily ON daily(tag_id, day);
    CREATE INDEX ix_raw ON raw(tag_id, ts);
    """)
    tid = 0
    ids: dict[str, int] = {}
    legacy: dict[str, int] = {}
    for sig, s in w.signals.items():
        if not site_filter(s):
            continue
        tid += 1
        ids[sig] = tid
        pos = w.positions[s["pos"]]
        name = s["tag"]
        desc = s["desc"].upper()
        pinned = sig in w.raw or w.signals[sig]["tag"] in ("50P503A.VIB_DE", "50P503A.VIB_NDE")
        if system == "PI" and s["quantity"] != "suction_pressure" and not pinned and s["site"] != "site:R2":
            r = w.rng.random()
            if r < 0.03:  # tag typed without the area prefix; the descriptor still names the position
                name = name[2:].replace(".", "_")
            elif r < 0.04:  # an orphan point with no usable description
                name, desc = f"PT{tid:04d}", ""
        s = dict(s, tag=name, desc=desc)
        unit = s["eng_unit"]
        alarm = s["alarm_high"]
        if s["site"] == "site:R3" and s["quantity"].startswith("vibration"):
            unit, alarm = "in/s", (round(alarm / 25.4, 3) if alarm else None)
        asset = None
        if s["site"] != "site:FA" and w.rng.random() < 0.9:
            asset = f"\\\\{pos['prefix']}\\{pos['tag'].split('-', 1)[1]}"
        if s["site"] == "site:FA" or not s["desc"]:
            asset = None
        con.execute("INSERT INTO tags VALUES(?,?,?,?,?,?,?,?,?)", (tid, s["tag"], s["desc"].upper(), unit, "DCS" if system == "PI" else "VSD",
                                                                  asset, alarm, s["sample_s"], None))
        tr.add(system, "tags", s["tag"], s["pos"])
        if s["quantity"] == "suction_pressure":
            tr.add(system, "tags", s["tag"], s["pos"][:-1] + "B")
        if s["site"] == "site:R2":
            tid += 1
            legacy[sig] = tid
            lname = s["tag"].replace(".", "_")
            con.execute("INSERT INTO tags VALUES(?,?,?,?,?,?,?,?,?)", (tid, lname, s["desc"].upper(), unit, "DCS", None, alarm, 300, R2_MIGRATION.isoformat()))
            con.execute("INSERT INTO tag_alias VALUES(?,?,?)", (lname, s["tag"], R2_MIGRATION.isoformat()))
            tr.add(system, "tags", lname, s["pos"])
            if s["quantity"] == "suction_pressure":
                tr.add(system, "tags", lname, s["pos"][:-1] + "B")
    rows = []
    mig = (R2_MIGRATION - HIST_START).days
    for sig, t in ids.items():
        s = w.signals[sig]
        d = w.daily.get(sig)
        if d is None:
            continue
        mean, mn, mx = (_conv(w, s, d[k]) for k in ("mean", "min", "max"))
        n = d["n"]
        for i in range(N):
            if np.isnan(mean[i]):
                continue
            tt = legacy[sig] if (sig in legacy and i < mig) else t
            nb = int(w.rng.random() < 0.01) * int(w.rng.integers(1, 6))
            rows.append((tt, DATES[i].isoformat(), float(round(mean[i], 4)), float(round(mn[i], 4)), float(round(mx[i], 4)), int(n[i]) - nb, nb))
    con.executemany("INSERT INTO daily VALUES(?,?,?,?,?,?,?)", rows)
    flat = w.answer["flatline"]["signal"]
    for sig, (ts, vals) in w.raw.items():
        if sig not in ids:
            continue
        s = w.signals[sig]
        v = _conv(w, s, vals)
        q = np.full(len(v), "Good", dtype=object)
        if sig == flat:
            q[:] = "Uncertain"
        con.executemany("INSERT INTO raw VALUES(?,?,?,?)", ((ids[sig], str(ts[k]).replace("T", " ") + "Z", float(round(v[k], 4)), q[k]) for k in range(len(v))))
    for a in alarms(w):
        if a["sig"] in ids:
            s = w.signals[a["sig"]]
            lim = a["limit"] / 25.4 if (s["site"] == "site:R3" and s["quantity"].startswith("vibration")) else a["limit"]
            val = a["value"] / 25.4 if (s["site"] == "site:R3" and s["quantity"].startswith("vibration")) else a["value"]
            con.execute("INSERT INTO alarms VALUES(?,?,?,?,?)", (ids[a["sig"]], a["ts"].strftime("%Y-%m-%d %H:%M:%SZ"), round(val, 4), round(lim, 4), a["state"]))
    if system == "SCADA":
        con.executescript("CREATE TABLE drive_events(well TEXT, ts TEXT, type TEXT, value REAL, note TEXT);")
        for e in drive_events(w):
            con.execute("INSERT INTO drive_events VALUES(?,?,?,?,?)", (e["well"], e["ts"].strftime("%Y-%m-%d %H:%M:%SZ"), e["type"], e["value"], e["note"]))
    else:
        con.executescript("CREATE TABLE cms_spectra(tag TEXT, day TEXT, f1x REAL, f2x REAL, bpfo REAL, bpfi REAL, bsf REAL, overall REAL);")
        for r in w.spectra:
            con.execute("INSERT INTO cms_spectra VALUES(?,?,?,?,?,?,?,?)", (r["tag"], r["on"].isoformat(), r["1x"], r["2x"], r["bpfo"], r["bpfi"], r["bsf"], r["overall"]))
    con.commit()
    con.close()


def render_engineering(w: World, out: Path, tr: Truth) -> None:
    # DEXPI-flavoured P&ID export
    drawings: dict[str, dict] = {}
    for pid, pos in w.positions.items():
        if pos["kind"] != "pump":
            continue
        dr = drawings.setdefault(pos["pid"], {"Drawing": pos["pid"], "Revision": pos["pid_rev"], "Site": pos["site"].split(":")[1], "PlantItems": []})
        dr["PlantItems"].append({"TagName": pos["tag"], "ComponentClass": "CentrifugalPump",
                                 "Attributes": {"DesignFlowM3h": pos["rated_m3h"], "ApiType": pos["api"]}})
        tr.add("P&ID", "PlantItem", pos["tag"], pid)
    for pid, pos in w.positions.items():
        if pos["kind"] == "pump" and pos["letter"] == "A":
            tag = f"{pos['area']}-PI-{1000 + pos['svc_idx'] + 3}"
            drawings[pos["pid"]]["PlantItems"].append({"TagName": tag, "ComponentClass": "PressureIndicator",
                                                       "Attributes": {"Service": "pump suction"},
                                                       "ConnectedTo": [pos["tag"], pos["tag"][:-1] + "B"]})
    (out / "pid_dexpi.json").write_text(json.dumps({"Format": "DEXPI-like (synthetic)", "Drawings": list(drawings.values())}, indent=1))
    with open(out / "edms_documents.csv", "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["doc_no", "kind", "revision", "status", "title", "applies_to"])
        for d in w.documents:
            cw.writerow([d["no"], d["kind"], d["rev"], "IFU", d["title"], ";".join(d["applies"])])
            for a in d["applies"]:
                if d["kind"] in ("datasheet", "P&ID"):
                    for p in w.positions.values():
                        if p["tag"] == a and p["site"] == d["site"]:
                            tr.add("EDMS", "doc_applies", f"{d['no']}|{a}", p["id"])
    wells = []
    for pid, pos in w.positions.items():
        if pos["kind"] == "well":
            wells.append({"WellID": f"osdu:master-data--Well:FA-{pos['tag'].replace('-', '')}", "FacilityName": f"Well {pos['tag']}", "Field": "Field A",
                          "Pad": pos["pad"], "LiftMethod": pos["lift"], "Spud": str(date(2018, 1, 1) + timedelta(days=int(w.rng.integers(0, 1200))))})
            tr.add("OSDU", "Well", wells[-1]["WellID"], pid)
    (out / "osdu_wells.json").write_text(json.dumps({"results": wells}, indent=1))
    ecos = [dict(no=e["id"], title=e["title"], part=e["part"], route=e["route"].upper(), approved=e["approved"].isoformat(),
                 qualification_test_waived="Y" if e["waived"] else "N", supplier_from=e["supplier_from"], supplier_to=e["supplier_to"],
                 status=e["status"], summary=e["summary"]) for e in w.ecos.values()]
    con = _db(out / "kestrel_plm.sqlite")
    con.executescript("CREATE TABLE eco(eco_no TEXT PRIMARY KEY, title TEXT, part TEXT, route TEXT, approved TEXT, qualification_test_waived TEXT, supplier_from TEXT, supplier_to TEXT, status TEXT, summary TEXT);")
    for e in ecos:
        con.execute("INSERT INTO eco VALUES(?,?,?,?,?,?,?,?,?,?)", tuple(e.values()))
        tr.add("PLM", "eco", e["no"], f"eco:{e['no']}")
    con.commit()
    con.close()


def render_maker(w: World, out: Path, tr: Truth) -> None:
    code = {oid: f"S{100 + i}" for i, oid in enumerate(ORGS)}
    for l in w.lots.values():
        if l["material"] == "mechanical seal faces" and l["received"] >= date(2025, 4, 15) and l["eco"] is None:
            l["eco"] = "ECO-25-0112"
    con = _db(out / "kestrel_mes.sqlite")
    con.executescript("""
    CREATE TABLE build_records(serial TEXT PRIMARY KEY, model TEXT, built TEXT, work_order TEXT, line TEXT);
    CREATE TABLE genealogy(serial TEXT, component_kind TEXT, lot_id TEXT);
    CREATE TABLE lots(lot_id TEXT PRIMARY KEY, material TEXT, supplier_code TEXT, received TEXT, po_no TEXT, qty INTEGER);
    CREATE TABLE test_records(serial TEXT, test_kind TEXT, value REAL, unit TEXT, passed INTEGER, tested TEXT);
    CREATE TABLE assembly(parent_serial TEXT, component_serial TEXT);
    """)
    for b in w.builds:
        con.execute("INSERT INTO build_records VALUES(?,?,?,?,?)", (b["serial"], b["model"], b["built"].isoformat(), b["wo"], b["line"]))
        tr.add("MES", "build_records", b["serial"], f"unit:{b['serial']}")
    for g in w.genealogy:
        con.execute("INSERT INTO genealogy VALUES(?,?,?)", (g["serial"], g["kind"], g["lot"]))
    for l in w.lots.values():
        con.execute("INSERT INTO lots VALUES(?,?,?,?,?,?)", (l["id"], l["material"], code[l["supplier"]], l["received"].isoformat(), l["po"], l["qty"]))
        tr.add("MES", "lots", l["id"], f"lot:{l['id']}")
    for t in w.tests:
        con.execute("INSERT INTO test_records VALUES(?,?,?,?,?,?)", (t["serial"], t["kind"], t["value"], t["unit"], int(t["passed"]), t["on"].isoformat()))
    for u in w.units.values():
        if u.get("parent"):
            con.execute("INSERT INTO assembly VALUES(?,?)", (w.units[u["parent"]]["serial"], u["serial"]))
    con.commit()
    con.close()
    con = _db(out / "kestrel_erp.sqlite")
    con.executescript("""
    CREATE TABLE customers(customer_no TEXT PRIMARY KEY, name TEXT);
    CREATE TABLE suppliers(supplier_code TEXT PRIMARY KEY, name TEXT);
    CREATE TABLE shipments(delivery_no TEXT, serial_no TEXT, customer_no TEXT, ship_date TEXT);
    CREATE TABLE lot_eco_effectivity(lot_id TEXT, eco_no TEXT);
    """)
    for c in w.customers.values():
        con.execute("INSERT INTO customers VALUES(?,?)", (c["no"], c["name"]))
    for oid, c in code.items():
        con.execute("INSERT INTO suppliers VALUES(?,?)", (c, ORGS[oid][0]))
    for s in w.shipments:
        con.execute("INSERT INTO shipments VALUES(?,?,?,?)", (s["delivery"], s["serial"], w.customers[s["customer"]]["no"], s["shipped"].isoformat()))
        tr.add("ERP", "shipments", f"{s['delivery']}|{s['serial']}", f"unit:{s['serial']}")
    con.commit()
    con.close()
    # PLM: record which lot an ECO governs only through the effectivity rule (part + supplier + date), not by lot id
    con = sqlite3.connect(out / "kestrel_plm.sqlite")
    con.executescript("CREATE TABLE IF NOT EXISTS eco_effectivity(eco_no TEXT, part TEXT, supplier_code TEXT, effective_from TEXT);")
    for e in w.ecos.values():
        if e["route"] == "expedited":
            con.execute("INSERT INTO eco_effectivity VALUES(?,?,?,?)", (e["id"], e["part"], code[e["supplier_to"]], e["approved"].isoformat()))
    con.commit()
    con.close()
    for l in w.lots.values():
        if l["eco"]:
            tr.add("TRUTH", "lot_eco", l["id"], f"eco:{l['eco']}")
    con = _db(out / "kestrel_qms.sqlite")
    con.executescript("""
    CREATE TABLE warranty_claims(claim_no TEXT PRIMARY KEY, customer_no TEXT, opened TEXT, status TEXT, narrative TEXT);
    CREATE TABLE claim_units(claim_no TEXT, serial_no TEXT);
    CREATE TABLE eightd(eightd_no TEXT PRIMARY KEY, title TEXT, status TEXT);
    """)
    for c in w.claims:
        con.execute("INSERT INTO warranty_claims VALUES(?,?,?,?,?)", (c["no"], w.customers[c["customer"]]["no"], c["opened"].isoformat(), c["status"], c["narrative"]))
        for s in c["serials"]:
            con.execute("INSERT INTO claim_units VALUES(?,?)", (c["no"], s))
    con.commit()
    con.close()


def render_operator_it(w: World, out: Path, tr: Truth) -> None:
    with open(out / "reliability_runlife.csv", "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["well", "string_serial", "set_date", "pull_date", "pull_reason"])
        for r in sorted(w.runs, key=lambda r: (r["well"], r["start"])):
            cw.writerow([r["well"], w.units[r["unit"]]["serial"], r["start"].isoformat(), r["end"].isoformat() if r["end"] else "", r["pull_reason"] or ""])
            tr.add("RELIABILITY", "runlife", f"{r['well']}|{w.units[r['unit']]['serial']}", f"pos:FA:{r['well']}-ESP")
    with open(out / "difa_reports.csv", "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["difa_no", "string_serial", "well", "report_date", "standard", "finding"])
        for k, d in enumerate(w.difa, 1):
            cw.writerow([f"DIFA-{d['on'].year}-{k:03d}", w.units[d["unit"]]["serial"], d["well"], d["on"].isoformat(), d["standard"], d["finding"]])
    con = _db(out / "production.sqlite")
    con.executescript("""
    CREATE TABLE allocation(well TEXT, day TEXT, oil_bbl_d REAL);
    CREATE TABLE rigs(rig TEXT, free_from TEXT, note TEXT);
    CREATE TABLE windows(site TEXT, unit TEXT, opens TEXT, closes TEXT, kind TEXT);
    """)
    rows = []
    for key, d in w.daily.items():
        if key.startswith("prod:"):
            rows += [(key[5:], DATES[i].isoformat(), float(round(d["oil"][i], 1))) for i in range(N)]
    con.executemany("INSERT INTO allocation VALUES(?,?,?)", rows)
    for r in w.rigs:
        con.execute("INSERT INTO rigs VALUES(?,?,?)", (r["rig"], r["free_from"].isoformat(), r["note"]))
    for x in w.windows:
        con.execute("INSERT INTO windows VALUES(?,?,?,?,?)", (x["site"].split(":")[1], x["unit"], x["opens"].isoformat(), x["closes"].isoformat(), x["kind"]))
    con.commit()
    con.close()


def render_uns(w: World, out: Path) -> None:
    """Unified-namespace replay of the last six hours of the alarmed tags (Sparkplug-flavoured JSON lines)."""
    cut = np.datetime64(NOW.replace(tzinfo=None) - timedelta(hours=6))
    lines = []
    for sig in ("sig:R1:10P101A.VIB_DE", "sig:FA:A07_MTR_T"):
        s = w.signals[sig]
        pos = w.positions[s["pos"]]
        ts, vals = w.raw[sig]
        topic = (f"aurelia/{pos['site'].split(':')[1].lower()}/{pos.get('prefix', 'fielda').lower()}/{pos['tag'].replace(' ', '').lower()}/{s['quantity']}"
                 if s["site"] != "site:FA" else f"aurelia/fa/{pos['pad'].lower()}/{pos['tag'].replace(' ', '-').lower()}/{s['quantity']}")
        for k in np.nonzero(ts >= cut)[0]:
            lines.append((ts[k], json.dumps({"topic": topic, "ts": str(ts[k]) + "Z", "value": round(float(vals[k]), 3), "unit": s["eng_unit"], "quality": "Good"})))
    lines.sort()
    (out / "uns_replay.jsonl").write_text("\n".join(l for _, l in lines) + "\n")


def render_all(w: World, out: Path) -> Truth:
    out.mkdir(parents=True, exist_ok=True)
    tr = Truth()
    render_sap(w, out, tr)
    _hist_db(w, out, "historian_pi.sqlite", lambda s: s["site"] != "site:FA", tr, "PI")
    _hist_db(w, out, "scada_fielda.sqlite", lambda s: s["site"] == "site:FA", tr, "SCADA")
    render_engineering(w, out, tr)
    render_maker(w, out, tr)
    render_operator_it(w, out, tr)
    render_uns(w, out)
    return tr
