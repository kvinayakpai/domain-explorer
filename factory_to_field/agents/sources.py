"""Where the tools get plant data: straight from the generated files (FileSource) or over HTTP from the system simulators (HttpSource).

Both answer the same questions with the same shapes, so the agents cannot tell the difference and the gold cases pass either way.
HttpSource speaks the simulators' REST dialects: PI Web API, an OPC UA gateway for SCADA, SAP OData v2, OSDU search and storage, PLM, MES, QMS, production planning.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import urllib.parse
import urllib.request
from pathlib import Path


class SourceError(RuntimeError):
    pass


# ======================================================================================= files
class FileSource:
    kind = "files"

    def __init__(self, world: Path) -> None:
        self.w = Path(world)

    def _c(self, name: str) -> sqlite3.Connection:
        c = sqlite3.connect(self.w / name)
        c.row_factory = sqlite3.Row
        return c

    # ---- historian (PI + SCADA)
    def point(self, tag: str) -> dict | None:
        for system, f in (("PI", "historian_pi.sqlite"), ("SCADA", "scada_fielda.sqlite")):
            c = self._c(f)
            a = c.execute("SELECT current_name FROM tag_alias WHERE legacy_name=?", (tag,)).fetchone()
            r = c.execute("SELECT * FROM tags WHERE name=?", (a[0] if a else tag,)).fetchone()  # a retired name resolves to its replacement
            if r is not None:
                legacy = [dict(x) for x in c.execute("SELECT legacy_name AS name, migrated_on FROM tag_alias WHERE current_name=?", (r["name"],))]
                return {"system": system, "name": r["name"], "descriptor": r["descriptor"], "unit": r["engunits"], "alarm_high": r["alarm_high"], "retired": r["retired"], "legacy": legacy}
        return None

    def _tid(self, name: str) -> tuple[sqlite3.Connection, int]:
        for f in ("historian_pi.sqlite", "scada_fielda.sqlite"):
            c = self._c(f)
            r = c.execute("SELECT tag_id FROM tags WHERE name=?", (name,)).fetchone()
            if r:
                return c, r[0]
        raise SourceError(f"unknown tag {name}")

    def daily(self, name: str, after_day: str, upto_day: str, before_day: str | None = None) -> list[dict]:
        c, t = self._c_t(name)
        q = "SELECT day, mean, max, n_good FROM daily WHERE tag_id=? AND day>? AND day<=?" + (" AND day<?" if before_day else "") + " ORDER BY day"
        return [dict(r) for r in c.execute(q, (t, after_day, upto_day) + ((before_day,) if before_day else ()))]

    def _c_t(self, name):
        return self._tid(name)

    def raw(self, name: str, from_ts: str, upto_ts: str) -> list[dict]:
        c, t = self._tid(name)
        return [dict(r) for r in c.execute("SELECT ts, value, quality FROM raw WHERE tag_id=? AND ts>=? AND ts<=? ORDER BY ts", (t, from_ts, upto_ts))]

    def alarms(self, name: str, upto_ts: str) -> list[dict]:
        c, t = self._tid(name)
        return [dict(r) for r in c.execute("SELECT ts, value, limit_value, state FROM alarms WHERE tag_id=? AND ts<=? ORDER BY ts", (t, upto_ts))]

    def spectra(self, name: str, upto_day: str, limit: int | None = None, after_day: str | None = None) -> list[dict]:
        c = self._c("historian_pi.sqlite")
        if limit:
            return [dict(r) for r in c.execute("SELECT * FROM cms_spectra WHERE tag=? AND day<=? ORDER BY day DESC LIMIT ?", (name, upto_day, limit))]
        return [dict(r) for r in c.execute("SELECT * FROM cms_spectra WHERE tag=? AND day>? AND day<=?", (name, after_day or "0000", upto_day))]

    # ---- SAP PM
    def flocs(self, suffix: str) -> list[str]:
        return [r["tplnr"] for r in self._c("sap_pm.sqlite").execute("SELECT tplnr FROM IFLOT WHERE tplnr LIKE ?", (f"%{suffix}",))]

    def open_orders(self, flocs: list[str], upto_day: str) -> list[dict]:
        c = self._c("sap_pm.sqlite")
        return [dict(r) for r in c.execute(f"SELECT aufnr, ktext, istat, gstrp FROM AUFK WHERE tplnr IN ({','.join('?' * len(flocs))}) AND istat NOT IN ('TECO','CLSD') AND gstrp<=?", (*flocs, upto_day))]

    def notifications(self, suffix: str, upto_day: str, limit: int) -> list[dict]:
        return [dict(r) for r in self._c("sap_pm.sqlite").execute("SELECT qmnum, qmart, qmtxt, ltxt, qmdat, fecod, qmst FROM QMEL WHERE tplnr LIKE ? AND qmdat<=? ORDER BY qmdat DESC LIMIT ?", (f"%{suffix}", upto_day, limit))]

    def stock(self, text: str, site: str) -> list[dict]:
        return [dict(r) for r in self._c("sap_pm.sqlite").execute("SELECT matnr, maktx, werks, lgort, labst, wzeit FROM MARD WHERE maktx LIKE ? AND werks=?", (f"%{text}%", site))]

    # ---- production planning
    def windows(self, site: str, from_day: str) -> list[dict]:
        return [dict(r) for r in self._c("production.sqlite").execute("SELECT unit, opens, closes, kind FROM windows WHERE site=? AND opens>=? ORDER BY opens", (site, from_day))]

    def rigs(self) -> list[dict]:
        return [dict(r) for r in self._c("production.sqlite").execute("SELECT rig, free_from, note FROM rigs ORDER BY free_from")]

    def allocation(self, well: str, upto_day: str) -> dict | None:
        r = self._c("production.sqlite").execute("SELECT day, oil_bbl_d FROM allocation WHERE well=? AND day<=? ORDER BY day DESC LIMIT 1", (well, upto_day)).fetchone()
        return dict(r) if r else None

    # ---- maker: PLM, MES, QMS, OSDU
    def eco(self, no: str) -> dict | None:
        r = self._c("kestrel_plm.sqlite").execute("SELECT * FROM eco WHERE eco_no=?", (no,)).fetchone()
        return dict(r) if r else None

    def lot_change(self, lot: str) -> dict | None:
        m = self._c("kestrel_mes.sqlite").execute("SELECT * FROM lots WHERE lot_id=?", (lot,)).fetchone()
        if not m:
            return None
        e = self._c("kestrel_plm.sqlite").execute("""SELECT e.eco_no, e.title, e.route, e.qualification_test_waived, e.approved, e.summary, f.effective_from FROM eco_effectivity f JOIN eco e ON e.eco_no=f.eco_no
                     WHERE f.part=? AND f.supplier_code=? AND f.effective_from<=? ORDER BY f.effective_from DESC LIMIT 1""", (m["material"], m["supplier_code"], m["received"])).fetchone()
        return {"lot": lot, "material": m["material"], "supplier_code": m["supplier_code"], "received": m["received"], **(dict(e) if e else {"eco_no": None})}

    def lot_tests(self, lot: str, kind: str) -> dict | None:
        c = self._c("kestrel_mes.sqlite")
        mat = c.execute("SELECT material FROM lots WHERE lot_id=?", (lot,)).fetchone()
        if not mat:
            return None
        q = """SELECT AVG(t.value) v, COUNT(*) n FROM test_records t JOIN genealogy g ON g.serial=t.serial JOIN lots l ON l.lot_id=g.lot_id WHERE t.test_kind=? AND l.material=? AND {}"""
        a = c.execute(q.format("g.lot_id=?"), (kind, mat[0], lot)).fetchone()
        b = c.execute(q.format("g.lot_id<>?"), (kind, mat[0], lot)).fetchone()
        return {"lot": lot, "test_kind": kind, "lot_avg": a["v"], "lot_n": a["n"], "other_avg": b["v"], "other_n": b["n"]}

    def test_records(self, serial: str) -> list[dict]:
        return [dict(r) for r in self._c("kestrel_mes.sqlite").execute("SELECT test_kind, value, unit, passed, tested FROM test_records WHERE serial=?", (serial,))]

    def claims(self, serial: str | None) -> list[dict]:
        c = self._c("kestrel_qms.sqlite")
        cur = c.execute("SELECT w.* FROM warranty_claims w JOIN claim_units u ON u.claim_no=w.claim_no WHERE u.serial_no=?", (serial,)) if serial else c.execute("SELECT * FROM warranty_claims")
        return [dict(r) for r in cur]

    def difa(self, well: str | None, upto_day: str) -> list[dict]:
        with open(self.w / "difa_reports.csv", newline="") as f:
            return [r for r in csv.DictReader(f) if r["report_date"] <= upto_day and (well is None or r["well"] == well)]

    def well_master(self, well: str) -> dict | None:
        for r in json.loads((self.w / "osdu_wells.json").read_text())["results"]:
            if r["FacilityName"] == f"Well {well}":
                return r
        return None


# ======================================================================================= HTTP
class HttpSource:
    """Talks to the simulators. `token` is a read-only credential: the simulators refuse writes made with it."""
    kind = "http"

    def __init__(self, base: str, token: str = "ro-agent") -> None:
        self.base, self.token = base.rstrip("/"), token
        self._wid: dict[str, dict] = {}

    # -- plumbing
    def get(self, path: str, **params) -> dict:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, quote_via=urllib.parse.quote)
        req = urllib.request.Request(f"{self.base}{path}" + (f"?{qs}" if qs else ""), headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            raise SourceError(f"{e.code} {path}: {e.read()[:200]!r}") from e

    def post(self, path: str, body: dict, token: str | None = None, headers: dict | None = None) -> dict:
        req = urllib.request.Request(f"{self.base}{path}", data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {token or self.token}", "Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise SourceError(f"{e.code} {path}: {e.read()[:300].decode(errors='replace')}") from e

    @staticmethod
    def odata(resp: dict) -> list[dict]:
        return resp.get("d", {}).get("results", [])

    @staticmethod
    def q(s: str) -> str:
        return "'" + s.replace("'", "''") + "'"

    # -- historian
    def point(self, tag: str) -> dict | None:
        for system in ("PI", "SCADA"):
            if system == "PI":
                items = self.get("/piwebapi/points", nameFilter=tag).get("Items", [])
                p = next((i for i in items if i["Name"] == tag), None)
                if p:
                    attrs = self.get(f"/piwebapi/points/{p['WebId']}/attributes")
                    cur = attrs.get("successor")
                    if cur:  # retired tag: follow it to its replacement
                        items = self.get("/piwebapi/points", nameFilter=cur).get("Items", [])
                        p = next(i for i in items if i["Name"] == cur)
                        attrs = self.get(f"/piwebapi/points/{p['WebId']}/attributes")
                    legacy = self.get("/piwebapi/points", successorOf=p["Name"]).get("Items", [])
                    for x in legacy:
                        self._wid[x["Name"]] = {"system": "PI", "id": x["WebId"]}
                    self._wid[p["Name"]] = {"system": "PI", "id": p["WebId"]}
                    return {"system": "PI", "name": p["Name"], "descriptor": p["Descriptor"], "unit": p["EngineeringUnits"], "alarm_high": attrs.get("alarmhigh"),
                            "retired": attrs.get("retired"), "legacy": [{"name": x["Name"], "migrated_on": x["MigratedOn"]} for x in legacy]}
            else:
                nodes = self.get("/scada/v1/nodes", name=tag).get("nodes", [])
                n = next((x for x in nodes if x["browseName"] == tag), None)
                if n:
                    self._wid[n["browseName"]] = {"system": "SCADA", "id": n["nodeId"]}
                    return {"system": "SCADA", "name": n["browseName"], "descriptor": n["description"], "unit": n["unit"], "alarm_high": n["alarmHigh"], "retired": None, "legacy": []}
        return None

    def _handle(self, name: str) -> dict:
        if name not in self._wid:
            if self.point(name) is None:
                raise SourceError(f"unknown tag {name}")
        return self._wid[name]

    @staticmethod
    def _pi_ts(ts: str) -> str:  # "2026-10-16 07:30:00Z" -> ISO 8601
        return ts.replace(" ", "T")

    def daily(self, name: str, after_day: str, upto_day: str, before_day: str | None = None) -> list[dict]:
        h = self._handle(name)
        if h["system"] == "PI":
            mx = self.get(f"/piwebapi/streams/{h['id']}/summary", startTime=after_day, endTime=upto_day, summaryType="Maximum", summaryDuration="1d", boundaryType="after")
            av = self.get(f"/piwebapi/streams/{h['id']}/summary", startTime=after_day, endTime=upto_day, summaryType="Average", summaryDuration="1d", boundaryType="after")
            m = {i["Value"]["Timestamp"][:10]: i["Value"]["Value"] for i in mx.get("Items", [])}
            a = {i["Value"]["Timestamp"][:10]: i["Value"]["Value"] for i in av.get("Items", [])}
            rows = [{"day": d, "mean": a.get(d), "max": m[d], "n_good": None} for d in sorted(m)]
        else:
            mx = self.get(f"/scada/v1/nodes/{h['id']}/history", fromDay=after_day, toDay=upto_day, aggregate="max", interval="1d").get("values", [])
            av = {v["t"][:10]: v["v"] for v in self.get(f"/scada/v1/nodes/{h['id']}/history", fromDay=after_day, toDay=upto_day, aggregate="avg", interval="1d").get("values", [])}
            rows = [{"day": v["t"][:10], "mean": av.get(v["t"][:10]), "max": v["v"], "n_good": None} for v in mx]
        return [r for r in rows if r["day"] > after_day and r["day"] <= upto_day and (before_day is None or r["day"] < before_day)]

    def raw(self, name: str, from_ts: str, upto_ts: str) -> list[dict]:
        h = self._handle(name)
        if h["system"] == "PI":
            items = self.get(f"/piwebapi/streams/{h['id']}/recorded", startTime=self._pi_ts(from_ts), endTime=self._pi_ts(upto_ts), maxCount=200000).get("Items", [])
            return [{"ts": i["Timestamp"].replace("T", " "), "value": i["Value"], "quality": "Good" if i["Good"] and not i["Questionable"] else "Uncertain"} for i in items]
        vals = self.get(f"/scada/v1/nodes/{h['id']}/history", fromTs=self._pi_ts(from_ts), toTs=self._pi_ts(upto_ts)).get("values", [])
        return [{"ts": v["t"].replace("T", " "), "value": v["v"], "quality": v["q"]} for v in vals]

    def alarms(self, name: str, upto_ts: str) -> list[dict]:
        h = self._handle(name)
        if h["system"] == "PI":
            items = self.get("/piwebapi/eventframes", searchMode="StartInclusive", endTime=self._pi_ts(upto_ts), referencedElementName=name).get("Items", [])
            return [{"ts": i["StartTime"].replace("T", " "), "value": i["Value"], "limit_value": i["Limit"], "state": i["Severity"]} for i in items]
        al = self.get(f"/scada/v1/nodes/{h['id']}/alarms", toTs=self._pi_ts(upto_ts)).get("alarms", [])
        return [{"ts": a["t"].replace("T", " "), "value": a["value"], "limit_value": a["limit"], "state": a["state"]} for a in al]

    def spectra(self, name: str, upto_day: str, limit: int | None = None, after_day: str | None = None) -> list[dict]:
        return self.get("/cms/api/spectra", tag=name, to=upto_day, limit=limit, after=after_day).get("spectra", [])

    # -- SAP PM (OData v2)
    def flocs(self, suffix: str) -> list[str]:
        r = self.odata(self.get("/sap/opu/odata/sap/API_FUNCTIONALLOCATION/FunctionalLocation", **{"$filter": f"endswith(FunctionalLocation,{self.q(suffix)})"}))
        return [x["FunctionalLocation"] for x in r]

    def open_orders(self, flocs: list[str], upto_day: str) -> list[dict]:
        out = []
        for fl in flocs:
            r = self.odata(self.get("/sap/opu/odata/sap/API_MAINTENANCEORDER/MaintenanceOrder",
                                    **{"$filter": f"FunctionalLocation eq {self.q(fl)} and OrderStatus ne 'TECO' and OrderStatus ne 'CLSD' and ScheduledStart le {self.q(upto_day)}"}))
            out += [{"aufnr": x["MaintenanceOrder"], "ktext": x["OrderDescription"], "istat": x["OrderStatus"], "gstrp": x["ScheduledStart"]} for x in r]
        return out

    def notifications(self, suffix: str, upto_day: str, limit: int) -> list[dict]:
        r = self.odata(self.get("/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification",
                                **{"$filter": f"endswith(FunctionalLocation,{self.q(suffix)}) and NotificationDate le {self.q(upto_day)}", "$orderby": "NotificationDate desc", "$top": limit, "$expand": "to_LongText"}))
        return [{"qmnum": x["MaintenanceNotification"], "qmart": x["NotificationType"], "qmtxt": x["NotificationText"], "ltxt": (x.get("to_LongText") or {}).get("Text"),
                 "qmdat": x["NotificationDate"], "fecod": x["DamageCode"], "qmst": x["NotificationStatus"]} for x in r]

    def stock(self, text: str, site: str) -> list[dict]:
        r = self.odata(self.get("/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod", **{"$filter": f"substringof({self.q(text)},MaterialName) and Plant eq {self.q(site)}"}))
        return [{"matnr": x["Material"], "maktx": x["MaterialName"], "werks": x["Plant"], "lgort": x["StorageLocationName"], "labst": x["MatlWrhsStkQtyInMatBaseUnit"], "wzeit": x["PlannedDeliveryDurationInDays"]} for x in r]

    # -- production planning
    def windows(self, site: str, from_day: str) -> list[dict]:
        return self.get("/prod/api/windows", site=site, **{"from": from_day}).get("windows", [])

    def rigs(self) -> list[dict]:
        return self.get("/prod/api/rigs").get("rigs", [])

    def allocation(self, well: str, upto_day: str) -> dict | None:
        return self.get("/prod/api/allocation", well=well, to=upto_day).get("latest")

    # -- PLM, MES, QMS, OSDU
    def eco(self, no: str) -> dict | None:
        return self.get(f"/plm/api/changes/{urllib.parse.quote(no)}") or None

    def lot_change(self, lot: str) -> dict | None:
        m = self.get(f"/mes/api/lots/{urllib.parse.quote(lot)}")
        if not m:
            return None
        e = self.get("/plm/api/changes", part=m["material"], supplier=m["supplier_code"], effectiveOn=m["received"]).get("changes", [])
        return {"lot": lot, "material": m["material"], "supplier_code": m["supplier_code"], "received": m["received"], **(e[0] if e else {"eco_no": None})}

    def lot_tests(self, lot: str, kind: str) -> dict | None:
        return self.get(f"/mes/api/lots/{urllib.parse.quote(lot)}/test-summary", kind=kind) or None

    def test_records(self, serial: str) -> list[dict]:
        return self.get(f"/mes/api/units/{urllib.parse.quote(serial)}/tests").get("tests", [])

    def claims(self, serial: str | None) -> list[dict]:
        return self.get("/qms/api/claims", serial=serial).get("claims", [])

    def difa(self, well: str | None, upto_day: str) -> list[dict]:
        return self.get("/qms/api/difa", well=well, to=upto_day).get("reports", [])

    def well_master(self, well: str) -> dict | None:
        r = self.post("/osdu/api/search/v2/query", {"kind": "osdu:wks:master-data--Well:1.0.0", "query": f'data.FacilityName:"Well {well}"', "limit": 1})
        return (r.get("results") or [None])[0]


def make_source(world: Path, base_url: str | None = None):
    return HttpSource(base_url) if base_url else FileSource(world)


_ = re  # keep import for callers that build filters
