"""System simulators: one local HTTP server that speaks the dialects of the plant's systems, backed by the generated world.

    python -m factory_to_field.sim.server --port 8765

  /piwebapi/...                          AVEVA PI Web API (points, streams summary/recorded, event frames)   -- refinery historian
  /scada/v1/...                          OPC UA gateway REST (nodes, history, alarms)                          -- field SCADA / VSD
  /cms/api/spectra                       condition-monitoring vibration spectra
  /sap/opu/odata/sap/API_*               SAP S/4 PM OData v2 (functional locations, notifications, orders, stock; $filter $top $orderby $expand)
  /osdu/api/search/v2/query, /storage    OSDU search and storage (Well master data)
  /plm/api/..., /mes/api/..., /qms/api/...   the pump maker's PLM, MES and QMS
  /prod/api/...                          production planning (outage windows, rigs, allocation)
  /sim/health, /sim/writes               simulator housekeeping

Credentials are bearer tokens. `ro-agent` can read everything and write nothing. Writes need the `release` token plus
X-Approved-By and X-Draft-Id headers: that is the path a human approval takes (see agents/release.py). PI and SCADA refuse every write.
The simulators never see the answer key.
"""
from __future__ import annotations

import fnmatch
import json
import re
import sqlite3
import threading
import urllib.parse
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..agents.core import DEFAULT_WORLD

TOKENS = {"ro-agent": "read", "release": "release", "ops-readonly": "read"}


# ----------------------------------------------------------------------------------- mini OData engine
def _lit(s: str):
    s = s.strip()
    return s[1:-1].replace("''", "'") if s.startswith("'") else (float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else s)


def odata_filter(rows: list[dict], expr: str | None) -> list[dict]:
    if not expr:
        return rows
    clauses = re.split(r"\s+and\s+", expr)
    preds = []
    for c in clauses:
        c = c.strip()
        m = re.fullmatch(r"substringof\(('(?:[^']|'')*'),\s*(\w+)\)", c)
        if m:
            v, f = _lit(m.group(1)), m.group(2)
            preds.append(lambda r, v=v, f=f: v.lower() in str(r.get(f, "")).lower())
            continue
        m = re.fullmatch(r"(endswith|startswith)\((\w+),\s*('(?:[^']|'')*')\)", c)
        if m:
            fn, f, v = m.group(1), m.group(2), _lit(m.group(3))
            preds.append((lambda r, f=f, v=v: str(r.get(f, "")).endswith(v)) if fn == "endswith" else (lambda r, f=f, v=v: str(r.get(f, "")).startswith(v)))
            continue
        m = re.fullmatch(r"(\w+)\s+(eq|ne|le|ge|lt|gt)\s+('(?:[^']|'')*'|[-\d.]+)", c)
        if not m:
            raise ValueError(f"unsupported $filter clause: {c}")
        f, op, v = m.group(1), m.group(2), _lit(m.group(3))
        ops = {"eq": lambda a, b: a == b, "ne": lambda a, b: a != b, "le": lambda a, b: a <= b, "ge": lambda a, b: a >= b, "lt": lambda a, b: a < b, "gt": lambda a, b: a > b}
        preds.append(lambda r, f=f, op=op, v=v: r.get(f) is not None and ops[op](r[f], v))
    return [r for r in rows if all(p(r) for p in preds)]


def odata_response(rows: list[dict], q: dict) -> dict:
    rows = odata_filter(rows, q.get("$filter"))
    if q.get("$orderby"):
        f, _, d = q["$orderby"].partition(" ")
        rows = sorted(rows, key=lambda r: r.get(f) or "", reverse=d.strip().lower() == "desc")
    if q.get("$top"):
        rows = rows[: int(q["$top"])]
    return {"d": {"results": rows}}


# ----------------------------------------------------------------------------------- state
class State:
    def __init__(self, world: Path) -> None:
        self.w = Path(world)
        self.writes: list[dict] = []
        self.lock = threading.Lock()

    def c(self, name: str) -> sqlite3.Connection:
        c = sqlite3.connect(self.w / name)
        c.row_factory = sqlite3.Row
        return c

    def tag_rows(self, db: str) -> list[sqlite3.Row]:
        return self.c(db).execute("SELECT * FROM tags").fetchall()


def _sap(st: State, entity: str, expand: bool = False) -> list[dict]:
    c = st.c("sap_pm.sqlite")
    if entity == "FunctionalLocation":
        return [{"FunctionalLocation": r["tplnr"], "FunctionalLocationName": r["pltxt"], "SuperiorFunctionalLocation": r["tplma"], "MaintenancePlant": r["swerk"], "ObjectType": r["eqart"]} for r in c.execute("SELECT * FROM IFLOT")]
    if entity == "MaintenanceNotification":
        out = []
        for r in c.execute("SELECT * FROM QMEL"):
            d = {"MaintenanceNotification": r["qmnum"], "NotificationType": r["qmart"], "NotificationText": r["qmtxt"], "NotificationDate": r["qmdat"], "NotificationTime": r["mzeit"],
                 "FunctionalLocation": r["tplnr"], "Equipment": r["equnr"], "DamageCode": r["fecod"], "Priority": r["priok"], "NotificationStatus": r["qmst"]}
            if expand:
                d["to_LongText"] = {"Text": r["ltxt"]}
            out.append(d)
        return out
    if entity == "MaintenanceOrder":
        return [{"MaintenanceOrder": r["aufnr"], "OrderType": r["auart"], "OrderDescription": r["ktext"], "FunctionalLocation": r["tplnr"], "Equipment": r["equnr"], "ScheduledStart": r["gstrp"],
                 "ScheduledEnd": r["gltrp"], "OrderStatus": r["istat"], "MaintenanceNotification": r["qmnum"]} for r in c.execute("SELECT * FROM AUFK")]
    if entity == "A_MatlStkInAcctMod":
        return [{"Material": r["matnr"], "MaterialName": r["maktx"], "Plant": r["werks"], "StorageLocationName": r["lgort"], "MatlWrhsStkQtyInMatBaseUnit": r["labst"], "PlannedDeliveryDurationInDays": r["wzeit"]} for r in c.execute("SELECT * FROM MARD")]
    return []


SAP_ROUTES = {"API_FUNCTIONALLOCATION/FunctionalLocation": "FunctionalLocation", "API_MAINTNOTIFICATION/MaintenanceNotification": "MaintenanceNotification",
              "API_MAINTENANCEORDER/MaintenanceOrder": "MaintenanceOrder", "API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod": "A_MatlStkInAcctMod"}
WRITE_ROUTES = {"/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification": "SAP PM notification", "/sap/opu/odata/sap/API_MATERIAL_DOCUMENT_SRV/A_MaterialDocumentHeader": "SAP stock transfer",
                "/qms/api/claims": "QMS warranty claim", "/qms/api/eightd": "QMS 8D", "/qms/api/customer-notices": "QMS customer notice", "/prod/api/rigs/requests": "rig request", "/ops/api/operator-requests": "operator request"}


# ----------------------------------------------------------------------------------- handlers
def pi_points(st: State, q: dict) -> dict:
    rows = st.tag_rows("historian_pi.sqlite")
    c = st.c("historian_pi.sqlite")
    alias = {r["legacy_name"]: (r["current_name"], r["migrated_on"]) for r in c.execute("SELECT * FROM tag_alias")}
    items = []
    if "successorOf" in q:
        ids = {r["name"]: r["tag_id"] for r in rows}
        for legacy, (cur, mig) in alias.items():
            if cur == q["successorOf"] and legacy in ids:
                items.append({"WebId": f"F1DP{ids[legacy]:06d}", "Name": legacy, "MigratedOn": mig})
        return {"Items": items}
    pat = q.get("nameFilter", "*")
    for r in rows:
        if fnmatch.fnmatchcase(r["name"], pat):
            items.append({"WebId": f"F1DP{r['tag_id']:06d}", "Name": r["name"], "Descriptor": r["descriptor"], "EngineeringUnits": r["engunits"], "PointSource": r["pointsource"], "Path": r["asset_path"], "PointType": "Float32"})
    return {"Items": items}


def pi_attrs(st: State, tid: int) -> dict:
    c = st.c("historian_pi.sqlite")
    r = c.execute("SELECT * FROM tags WHERE tag_id=?", (tid,)).fetchone()
    if not r:
        return {}
    a = c.execute("SELECT current_name FROM tag_alias WHERE legacy_name=?", (r["name"],)).fetchone()
    return {"alarmhigh": r["alarm_high"], "retired": r["retired"], "sampleinterval": r["sample_s"], "successor": a[0] if a else None}


def _day_ts(d: str) -> str:
    return f"{d}T00:00:00Z"


def daily_rows(c: sqlite3.Connection, tid: int, start: str, end: str) -> list[sqlite3.Row]:
    return c.execute("SELECT day, mean, max FROM daily WHERE tag_id=? AND day>? AND day<=? ORDER BY day", (tid, start[:10], end[:10])).fetchall()


class Handler(BaseHTTPRequestHandler):
    state: State
    server_version = "PlantSim/1.0"

    def log_message(self, *a):  # quiet
        pass

    # -- plumbing
    def _send(self, code: int, body) -> None:
        raw = json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _auth(self) -> str | None:
        h = self.headers.get("Authorization", "")
        return TOKENS.get(h[7:]) if h.startswith("Bearer ") else None

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query, keep_blank_values=True).items()}
        if u.path == "/sim/health":
            return self._send(200, {"ok": True, "systems": ["PI Web API", "OPC UA gateway", "CMS", "SAP PM OData", "OSDU", "PLM", "MES", "QMS", "Production planning"], "writes": len(self.state.writes)})
        if self._auth() is None:
            return self._send(401, {"error": "bearer token required"})
        try:
            code, body = self.route_get(urllib.parse.unquote(u.path), q)
        except ValueError as e:
            code, body = 400, {"error": str(e)}
        self._send(code, body)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        role = self._auth()
        if role is None:
            return self._send(401, {"error": "bearer token required"})
        path = urllib.parse.unquote(u.path)
        if path == "/osdu/api/search/v2/query":  # a read, even though it is a POST
            return self._send(*self.osdu_search(body))
        if path.startswith("/piwebapi/") or path.startswith("/scada/"):
            return self._send(403, {"error": "this service account is read-only; OT writes go through the control room"})
        if path in WRITE_ROUTES:
            if role != "release":
                return self._send(403, {"error": "write refused: this credential is read-only"})
            who, draft = self.headers.get("X-Approved-By", "").strip(), self.headers.get("X-Draft-Id", "").strip()
            if not who or not draft:
                return self._send(403, {"error": "write refused: X-Approved-By and X-Draft-Id are required"})
            with self.state.lock:
                rec = {"id": f"{WRITE_ROUTES[path].split()[0]}-{len(self.state.writes) + 1:05d}", "system": WRITE_ROUTES[path], "path": path, "approved_by": who, "draft": draft, "body": body,
                       "at": datetime.now(UTC).isoformat(timespec="seconds")}
                self.state.writes.append(rec)
            return self._send(201, rec)
        self._send(404, {"error": "no such endpoint"})

    # -- routing
    def route_get(self, p: str, q: dict):
        st = self.state
        if p == "/sim/writes":
            return 200, {"writes": st.writes}
        # PI Web API
        if p == "/piwebapi/points":
            return 200, pi_points(st, q)
        m = re.fullmatch(r"/piwebapi/points/F1DP(\d+)/attributes", p)
        if m:
            return 200, pi_attrs(st, int(m.group(1)))
        m = re.fullmatch(r"/piwebapi/streams/F1DP(\d+)/(summary|recorded)", p)
        if m:
            tid, kind = int(m.group(1)), m.group(2)
            c = st.c("historian_pi.sqlite")
            if kind == "summary":
                col = "max" if q.get("summaryType") == "Maximum" else "mean"
                return 200, {"Items": [{"Type": q["summaryType"], "Value": {"Timestamp": _day_ts(r["day"]), "Value": r[col], "Good": True}} for r in daily_rows(c, tid, q["startTime"], q["endTime"])]}
            s, e = q["startTime"].replace("T", " "), q["endTime"].replace("T", " ")
            rows = c.execute("SELECT ts, value, quality FROM raw WHERE tag_id=? AND ts>=? AND ts<=? ORDER BY ts LIMIT ?", (tid, s, e, int(q.get("maxCount", 1000)))).fetchall()
            return 200, {"Items": [{"Timestamp": r["ts"].replace(" ", "T"), "Value": r["value"], "Good": r["quality"] == "Good", "Questionable": r["quality"] != "Good", "Substituted": False} for r in rows]}
        if p == "/piwebapi/eventframes":
            c = st.c("historian_pi.sqlite")
            r = c.execute("SELECT tag_id FROM tags WHERE name=?", (q["referencedElementName"],)).fetchone()
            rows = c.execute("SELECT ts, value, limit_value, state FROM alarms WHERE tag_id=? AND ts<=? ORDER BY ts", (r[0], q["endTime"].replace("T", " "))).fetchall() if r else []
            return 200, {"Items": [{"Name": f"Alarm {q['referencedElementName']}", "StartTime": x["ts"].replace(" ", "T"), "Value": x["value"], "Limit": x["limit_value"], "Severity": x["state"]} for x in rows]}
        # SCADA gateway
        if p == "/scada/v1/nodes":
            rows = [r for r in st.tag_rows("scada_fielda.sqlite") if fnmatch.fnmatchcase(r["name"], q.get("name", "*"))]
            return 200, {"nodes": [{"nodeId": f"FA.{r['tag_id']}", "browseName": r["name"], "description": r["descriptor"], "unit": r["engunits"], "alarmHigh": r["alarm_high"]} for r in rows]}
        m = re.fullmatch(r"/scada/v1/nodes/FA\.(\d+)/(history|alarms)", p)
        if m:
            tid, kind = int(m.group(1)), m.group(2)
            c = st.c("scada_fielda.sqlite")
            if kind == "alarms":
                rows = c.execute("SELECT ts, value, limit_value, state FROM alarms WHERE tag_id=? AND ts<=? ORDER BY ts", (tid, q["toTs"].replace("T", " "))).fetchall()
                return 200, {"alarms": [{"t": r["ts"].replace(" ", "T"), "value": r["value"], "limit": r["limit_value"], "state": r["state"]} for r in rows]}
            if "aggregate" in q:
                col = "max" if q["aggregate"] == "max" else "mean"
                return 200, {"values": [{"t": _day_ts(r["day"]), "v": r[col]} for r in daily_rows(c, tid, q["fromDay"], q["toDay"])]}
            rows = c.execute("SELECT ts, value, quality FROM raw WHERE tag_id=? AND ts>=? AND ts<=? ORDER BY ts", (tid, q["fromTs"].replace("T", " "), q["toTs"].replace("T", " "))).fetchall()
            return 200, {"values": [{"t": r["ts"].replace(" ", "T"), "v": r["value"], "q": r["quality"]} for r in rows]}
        if p == "/cms/api/spectra":
            c = st.c("historian_pi.sqlite")
            if q.get("limit"):
                rows = c.execute("SELECT * FROM cms_spectra WHERE tag=? AND day<=? ORDER BY day DESC LIMIT ?", (q["tag"], q["to"], int(q["limit"]))).fetchall()
            else:
                rows = c.execute("SELECT * FROM cms_spectra WHERE tag=? AND day>? AND day<=?", (q["tag"], q.get("after", "0000"), q["to"])).fetchall()
            return 200, {"spectra": [dict(r) for r in rows]}
        # SAP OData
        m = re.fullmatch(r"/sap/opu/odata/sap/(\w+/\w+)", p)
        if m and m.group(1) in SAP_ROUTES:
            return 200, odata_response(_sap(st, SAP_ROUTES[m.group(1)], expand="to_LongText" in q.get("$expand", "")), q)
        # OSDU storage
        m = re.fullmatch(r"/osdu/api/storage/v2/records/(.+)", p)
        if m:
            for r in json.loads((st.w / "osdu_wells.json").read_text())["results"]:
                if r["WellID"] == m.group(1):
                    return 200, {"id": r["WellID"], "kind": "osdu:wks:master-data--Well:1.0.0", "data": r}
            return 404, {}
        # production planning
        if p == "/prod/api/windows":
            rows = st.c("production.sqlite").execute("SELECT unit, opens, closes, kind FROM windows WHERE site=? AND opens>=? ORDER BY opens", (q["site"], q["from"])).fetchall()
            return 200, {"windows": [dict(r) for r in rows]}
        if p == "/prod/api/rigs":
            return 200, {"rigs": [dict(r) for r in st.c("production.sqlite").execute("SELECT rig, free_from, note FROM rigs ORDER BY free_from")]}
        if p == "/prod/api/allocation":
            r = st.c("production.sqlite").execute("SELECT day, oil_bbl_d FROM allocation WHERE well=? AND day<=? ORDER BY day DESC LIMIT 1", (q["well"], q["to"])).fetchone()
            return 200, {"latest": dict(r) if r else None}
        # PLM
        m = re.fullmatch(r"/plm/api/changes/(.+)", p)
        if m:
            r = st.c("kestrel_plm.sqlite").execute("SELECT * FROM eco WHERE eco_no=?", (m.group(1),)).fetchone()
            return (200, dict(r)) if r else (404, {})
        if p == "/plm/api/changes":
            rows = st.c("kestrel_plm.sqlite").execute("""SELECT e.eco_no, e.title, e.route, e.qualification_test_waived, e.approved, e.summary, f.effective_from FROM eco_effectivity f JOIN eco e ON e.eco_no=f.eco_no
                     WHERE f.part=? AND f.supplier_code=? AND f.effective_from<=? ORDER BY f.effective_from DESC LIMIT 1""", (q["part"], q["supplier"], q["effectiveOn"])).fetchall()
            return 200, {"changes": [dict(r) for r in rows]}
        # MES
        m = re.fullmatch(r"/mes/api/lots/([^/]+)(/test-summary)?", p)
        if m:
            c = st.c("kestrel_mes.sqlite")
            lot = c.execute("SELECT * FROM lots WHERE lot_id=?", (m.group(1),)).fetchone()
            if not lot:
                return 404, {}
            if not m.group(2):
                return 200, dict(lot)
            qq = "SELECT AVG(t.value) v, COUNT(*) n FROM test_records t JOIN genealogy g ON g.serial=t.serial JOIN lots l ON l.lot_id=g.lot_id WHERE t.test_kind=? AND l.material=? AND {}"
            a = c.execute(qq.format("g.lot_id=?"), (q["kind"], lot["material"], lot["lot_id"])).fetchone()
            b = c.execute(qq.format("g.lot_id<>?"), (q["kind"], lot["material"], lot["lot_id"])).fetchone()
            return 200, {"lot": lot["lot_id"], "test_kind": q["kind"], "lot_avg": a["v"], "lot_n": a["n"], "other_avg": b["v"], "other_n": b["n"]}
        m = re.fullmatch(r"/mes/api/units/([^/]+)/tests", p)
        if m:
            rows = st.c("kestrel_mes.sqlite").execute("SELECT test_kind, value, unit, passed, tested FROM test_records WHERE serial=?", (m.group(1),)).fetchall()
            return 200, {"tests": [dict(r) for r in rows]}
        # QMS
        if p == "/qms/api/claims":
            c = st.c("kestrel_qms.sqlite")
            cur = c.execute("SELECT w.* FROM warranty_claims w JOIN claim_units u ON u.claim_no=w.claim_no WHERE u.serial_no=?", (q["serial"],)) if q.get("serial") else c.execute("SELECT * FROM warranty_claims")
            return 200, {"claims": [dict(r) for r in cur]}
        if p == "/qms/api/difa":
            import csv
            with open(st.w / "difa_reports.csv", newline="") as f:
                rows = [r for r in csv.DictReader(f) if r["report_date"] <= q["to"] and (not q.get("well") or r["well"] == q["well"])]
            return 200, {"reports": rows}
        return 404, {"error": f"no such endpoint {p}"}

    def osdu_search(self, body: dict):
        m = re.search(r'FacilityName:"([^"]+)"', body.get("query", ""))
        rows = json.loads((self.state.w / "osdu_wells.json").read_text())["results"]
        hits = [r for r in rows if not m or r["FacilityName"] == m.group(1)][: int(body.get("limit", 100))]
        return 200, {"results": hits, "totalCount": len(hits)}


def make_server(world: Path = DEFAULT_WORLD, port: int = 0, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    st = State(world)
    handler = type("H", (Handler,), {"state": st})
    srv = ThreadingHTTPServer((host, port), handler)
    srv.state = st  # type: ignore[attr-defined]
    return srv


def serve_in_thread(world: Path = DEFAULT_WORLD, port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    srv = make_server(world, port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--world", type=Path, default=DEFAULT_WORLD)
    a = ap.parse_args()
    s = make_server(a.world, a.port, "0.0.0.0")
    print(f"plant system simulators on http://127.0.0.1:{a.port}  (tokens: ro-agent for reads; release for approved writes)")
    s.serve_forever()
