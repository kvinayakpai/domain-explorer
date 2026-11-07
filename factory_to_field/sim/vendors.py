"""Mock source systems: one dialect per vendor product, all backed by the same simulated plant.

The simulators in server.py cover the systems the agents read today (PI Web API, OPC UA gateway, SAP PM, OSDU, the pump
maker's PLM/MES/QMS, production planning). This module adds a mock for every other source system the oil and gas and plant
subdomains name (data/taxonomy/*.yaml: sourceSystems), so a connector can be written and tested against each one without a
real installation. Each mock lives under /v/<slug>/ and answers with that product's naming and response shapes:

  historians     proficy_historian aspenone aws_sitewise insights_hub cognite thingworx openenterprise pi_af
  control        deltav experion centum controllogix s7 wincc factorytalk
  EAM / CMMS     maximo maximo_eam eam (Infor)   [PM/EAM is SAP: the SAP simulator in server.py]
  vibration CM   system1 skf_observer ams senseye augury ecostruxure ft_analytics
  APM            apm ge_apm maximo_apm mas_apm aspen_mtell uptake asset_performance asset_intelligence_network assetwise
                 industrial_ai forge
  MES / MOM      opcenter ft_productioncentre proficy_pa digital_manufacturing
  ESP records    esp_difa

GET /v/ lists them. The data is the world's own (same tags, same alarms, same work orders and lots), renamed the way each
product names it, so the same fact can be found through several systems with different identifiers: that is the point.
These are interpretations of each product's API, not vendor-certified, and read-only. The health scores and alerts the
CM/APM mocks return are simple rules over the world's vibration data (see _health), not a vendor's model.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import urllib.parse
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

ASOF = "2026-10-17"
HIST, FIELD = "historian_pi.sqlite", "scada_fielda.sqlite"

# slug -> (name as the taxonomies write it, vendor, family, what it mirrors)
SYSTEMS: dict[str, tuple[str, str, str, str]] = {
    "proficy_historian": ("Proficy Historian / Plant Applications", "Proficy (GE Vernova, sold to TPG 2 Mar 2026)", "historian", "plant historian points"),
    "aspenone": ("aspenONE", "Aspen Technology", "historian", "IP.21 tags"),
    "aws_sitewise": ("SiteWise", "Amazon Web Services", "historian", "asset property aliases"),
    "insights_hub": ("Insights Hub (formerly MindSphere) / Industrial Edge", "Siemens", "historian", "asset aspects and time series"),
    "cognite": ("Cognite Data Fusion", "Cognite", "historian", "assets and time series"),
    "thingworx": ("ThingWorx (IIoT Platform)", "PTC", "historian", "things and property history"),
    "openenterprise": ("OpenEnterprise SCADA", "Emerson", "historian", "field SCADA points"),
    "pi_af": ("PI System / PI Asset Framework", "AVEVA", "historian", "AF elements and attributes"),
    "deltav": ("DeltaV", "Emerson", "control", "DCS modules"),
    "experion": ("Experion PKS", "Honeywell", "control", "DCS points"),
    "centum": ("CENTUM VP", "Yokogawa", "control", "DCS tags"),
    "controllogix": ("ControlLogix PLC", "Rockwell Automation", "control", "controller tags"),
    "s7": ("SIMATIC S7 PLC", "Siemens", "control", "data block addresses"),
    "wincc": ("WinCC", "Siemens", "control", "HMI tags"),
    "factorytalk": ("FactoryTalk", "Rockwell", "control", "FactoryTalk View tags"),
    "maximo": ("Maximo", "IBM", "eam", "work orders, assets, service requests"),
    "maximo_eam": ("Maximo EAM", "IBM", "eam", "work orders, assets, service requests"),
    "eam": ("EAM", "Infor", "eam", "work orders, equipment, requests"),
    "system1": ("Bently Nevada System 1", "Baker Hughes", "cm", "vibration measurements and alerts"),
    "skf_observer": ("SKF @ptitude Observer", "SKF", "cm", "vibration measurements and alerts"),
    "ams": ("AMS Machine Works", "Emerson", "cm", "vibration measurements and alerts"),
    "senseye": ("Senseye Predictive Maintenance", "Siemens", "cm", "vibration measurements and alerts"),
    "augury": ("Augury Machine Health", "Augury", "cm", "vibration measurements and alerts"),
    "ecostruxure": ("EcoStruxure Asset Advisor", "Schneider Electric", "cm", "vibration measurements and alerts"),
    "ft_analytics": ("FactoryTalk Analytics for Devices", "Rockwell Automation", "cm", "vibration measurements and alerts"),
    "apm": ("APM", "GE Vernova", "apm", "asset health and alerts"),
    "ge_apm": ("APM (Meridium, SmartSignal)", "GE Vernova", "apm", "asset health and alerts"),
    "maximo_apm": ("Maximo APM", "IBM", "apm", "asset health and alerts"),
    "mas_apm": ("Maximo Application Suite — APM", "IBM", "apm", "asset health and alerts"),
    "aspen_mtell": ("Aspen Mtell", "AspenTech", "apm", "asset health and alerts"),
    "uptake": ("Uptake APM", "Uptake", "apm", "asset health and alerts"),
    "asset_performance": ("Asset Performance", "AVEVA", "apm", "asset health and alerts"),
    "asset_intelligence_network": ("Asset Intelligence Network", "SAP", "apm", "asset health and alerts"),
    "assetwise": ("AssetWise", "Bentley", "apm", "asset health and alerts"),
    "industrial_ai": ("Industrial AI Platform", "Avathon (formerly SparkCognition)", "apm", "asset health and alerts"),
    "forge": ("Forge for Industrial", "Honeywell", "apm", "asset health and alerts"),
    "opcenter": ("Opcenter Execution", "Siemens", "mom", "work orders, lots, test results"),
    "ft_productioncentre": ("FactoryTalk ProductionCentre", "Rockwell Automation", "mom", "work orders, lots, test results"),
    "proficy_pa": ("Proficy Plant Applications", "Proficy (GE Vernova, sold to TPG 2 Mar 2026)", "mom", "work orders, lots, test results"),
    "digital_manufacturing": ("Digital Manufacturing", "SAP", "mom", "work orders, lots, test results"),
    "esp_difa": ("ESP surveillance and DIFA records", "Baker Hughes / SLB", "esp", "drive events and teardown reports"),
}


# ------------------------------------------------------------------------------------------------ world access
def _db(st, name: str) -> sqlite3.Connection:
    return st.c(name)


def _tags(st) -> list[dict]:
    out = []
    for db, site in ((HIST, "CDU1"), (FIELD, "FIELD_A")):
        for r in _db(st, db).execute("SELECT * FROM tags ORDER BY tag_id"):
            out.append({**dict(r), "db": db, "site": site})
    return out


def _split(name: str) -> tuple[str, str]:
    """('P101A', 'VIB_DE') from '10P101A.VIB_DE' or the legacy 'P101B_VIB_NDE'; ('A01', 'MTR_T') from 'A01_MTR_T'."""
    m = re.fullmatch(r"(?:\d{2})?([A-Z]+\d+[A-Z]?)[._](.+)", name)
    return (m.group(1), m.group(2)) if m else (name, "PV")


def _uid(prefix: str, key: str) -> str:
    return f"{prefix}-{hashlib.sha1(key.encode()).hexdigest()[:12]}"


def _bounds(q: dict, default_days: int = 30) -> tuple[str, str]:
    end = q.get("end") or q.get("endTime") or q.get("to") or f"{ASOF}T07:00:00Z"
    start = q.get("start") or q.get("startTime") or q.get("from") or (datetime.fromisoformat(end.replace("Z", "")) - timedelta(days=default_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return start, end


def _samples(st, t: dict, start: str, end: str, limit: int) -> list[tuple[str, float, bool]]:
    """Raw samples when the range sits inside the raw window, otherwise daily means."""
    c = _db(st, t["db"])
    s, e = start.replace("T", " "), end.replace("T", " ")
    if len(s) == 10:
        s += " 00:00:00Z"
    if len(e) == 10:
        e += " 23:59:59Z"
    rows = c.execute("SELECT ts, value, quality FROM raw WHERE tag_id=? AND ts>=? AND ts<=? ORDER BY ts LIMIT ?", (t["tag_id"], s, e, limit)).fetchall()
    if rows:
        return [(r["ts"].replace(" ", "T"), r["value"], r["quality"] == "Good") for r in rows]
    rows = c.execute("SELECT day, mean FROM daily WHERE tag_id=? AND day>=? AND day<=? ORDER BY day LIMIT ?", (t["tag_id"], s[:10], e[:10], limit)).fetchall()
    return [(f"{r['day']}T00:00:00Z", r["mean"], True) for r in rows if r["mean"] is not None]


def _find_tag(tags: list[dict], key: str, native) -> dict | None:
    for t in tags:
        if key in (t["name"], native(t)):
            return t
    return None


def _epoch(ts: str) -> int:
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=UTC).timestamp())


# ---------------------------------------------------------------------------------------------------- historians
def _hist_name(slug: str) -> Callable[[dict], str]:
    def n(t: dict) -> str:
        eq, ms = _split(t["name"])
        return {
            "proficy_historian": f"{t['site']}.{eq}.{ms}",
            "aspenone": f"{eq}_{ms}",
            "aws_sitewise": f"/{t['site']}/{eq}/{ms.lower()}",
            "insights_hub": f"{_uid('asset', eq)}/{ms}",
            "cognite": f"{'pi' if t['site'] == 'CDU1' else 'scada'}:{t['name']}",
            "thingworx": f"{eq}.{ms}",
            "openenterprise": f"{eq}:{ms}",
            "pi_af": f"\\\\AF\\{t['site']}\\{eq}|{ms}",
        }[slug]
    return n


def _hist_point(slug: str, t: dict, native: str) -> dict:
    eq, ms = _split(t["name"])
    base = {"name": native, "description": t["descriptor"], "unit": t["engunits"], "alarmHigh": t["alarm_high"]}
    if slug == "proficy_historian":
        return {"TagName": native, "Description": t["descriptor"], "EngineeringUnits": t["engunits"], "DataType": "Float", "Collector": t["site"]}
    if slug == "aws_sitewise":
        return {"propertyAlias": native, "assetId": _uid("sw", eq), "dataType": "DOUBLE", "unit": t["engunits"], "notification": {"state": "DISABLED"}}
    if slug == "insights_hub":
        return {"assetId": native.split("/")[0], "aspectName": ms.split("_")[0].title(), "variableName": ms, "unit": t["engunits"], "dataType": "DOUBLE"}
    if slug == "cognite":
        return {"id": int(hashlib.sha1(native.encode()).hexdigest()[:8], 16), "externalId": native, "name": t["descriptor"], "unit": t["engunits"], "isString": False, "assetId": int(hashlib.sha1(eq.encode()).hexdigest()[:7], 16)}
    if slug == "thingworx":
        return {"name": ms, "thing": eq, "baseType": "NUMBER", "description": t["descriptor"], "isPersistent": True, "logged": True}
    if slug == "pi_af":
        return {"Path": native, "Name": ms, "DefaultUnitsName": t["engunits"], "DataReferencePlugIn": "PI Point", "PointName": t["name"]}
    return base


def _hist_values(slug: str, native: str, t: dict, rows: list[tuple[str, float, bool]]) -> dict:
    if slug == "proficy_historian":
        return {"Data": {"Tag": {"TagName": native, "Samples": [{"TimeStamp": ts, "Value": v, "Quality": 192 if g else 0} for ts, v, g in rows]}}}
    if slug == "aspenone":
        return {"data": [{"name": native, "samples": [{"t": ts, "x": v, "l": "Good" if g else "Bad"} for ts, v, g in rows]}]}
    if slug == "aws_sitewise":
        return {"assetPropertyValueHistory": [{"value": {"doubleValue": v}, "timestamp": {"timeInSeconds": _epoch(ts), "offsetInNanos": 0}, "quality": "GOOD" if g else "BAD"} for ts, v, g in rows]}
    if slug == "insights_hub":
        return [{"_time": ts, t["name"].split(".")[-1]: v, "qualitycode": 0 if g else 1} for ts, v, g in rows]
    if slug == "cognite":
        return {"items": [{"id": _hist_point(slug, t, native)["id"], "externalId": native, "isString": False, "datapoints": [{"timestamp": _epoch(ts) * 1000, "value": v} for ts, v, _ in rows]}]}
    if slug == "thingworx":
        return {"dataShape": {"fieldDefinitions": {"timestamp": {"baseType": "DATETIME"}, "value": {"baseType": "NUMBER"}}}, "rows": [{"timestamp": _epoch(ts) * 1000, "value": v, "quality": "GOOD" if g else "BAD"} for ts, v, g in rows]}
    if slug == "openenterprise":
        return {"point": native, "history": [[ts, v, 0 if g else 192] for ts, v, g in rows]}
    return {"Path": native, "Items": [{"Timestamp": ts, "Value": v, "Good": g} for ts, v, g in rows]}


def _historian(st, slug: str, rest: str, q: dict):
    tags = [t for t in _tags(st) if slug != "openenterprise" or t["db"] == FIELD]
    native = _hist_name(slug)
    if rest in ("tags", ""):
        pat = q.get("filter", "")
        items = [_hist_point(slug, t, native(t)) for t in tags if pat.lower() in (native(t) + t["descriptor"]).lower()]
        lim, off = int(q.get("limit", 200)), int(q.get("offset", 0))
        key = {"cognite": "items", "proficy_historian": "Tags", "pi_af": "Items", "aspenone": "data"}.get(slug, "items")
        return 200, {key: items[off:off + lim], "total": len(items), "offset": off}
    if rest == "history":
        t = _find_tag(tags, q.get("tag", ""), native)
        if not t:
            return 404, {"error": f"no such tag {q.get('tag')!r} in {SYSTEMS[slug][0]}"}
        s, e = _bounds(q)
        return 200, _hist_values(slug, native(t), t, _samples(st, t, s, e, int(q.get("max", 1000))))
    return 404, {"error": "no such endpoint"}


# ------------------------------------------------------------------------------------------------ control systems
def _ctrl_name(slug: str, i: int, t: dict) -> str:
    eq, ms = _split(t["name"])
    return {
        "deltav": f"{eq}/{ms}/PV",
        "experion": f"{eq}_{ms.replace('_', '')}.PV",
        "centum": f"{eq}-{ms.replace('_', '-')}.PV",
        "controllogix": f"Program:Main.{eq}_{ms.title().replace('_', '')}",
        "s7": f"DB{100 + i // 40}.DBD{4 * (i % 40)}",
        "wincc": f"{t['site']}_{eq}_{ms}",
        "factorytalk": f"[{t['site']}]{eq}_{ms}",
    }[slug]


_ALARM_KEYS = {
    "deltav": ("EventType", "Module", "Level", "Time"),
    "experion": ("AlarmType", "Point", "Priority", "AlarmTime"),
    "centum": ("MessageType", "TagName", "AlarmStatus", "OccurredAt"),
    "controllogix": ("Type", "Tag", "Severity", "Timestamp"),
    "s7": ("AlarmClass", "Address", "State", "Time"),
    "wincc": ("Class", "Tag", "State", "DateTime"),
    "factorytalk": ("AlarmClass", "Source", "Severity", "TimeIn"),
}


def _control(st, slug: str, rest: str, q: dict):
    tags = _tags(st)
    named = [(_ctrl_name(slug, i, t), t) for i, t in enumerate(tags)]
    if rest in ("tags", ""):
        pat = q.get("filter", "").lower()
        items = [{"tag": n, "description": t["descriptor"], "unit": t["engunits"], "area": t["site"], **({"symbol": t["name"]} if slug == "s7" else {})} for n, t in named if pat in (n + t["descriptor"]).lower()]
        lim, off = int(q.get("limit", 200)), int(q.get("offset", 0))
        return 200, {"tags": items[off:off + lim], "total": len(items), "offset": off}
    if rest == "read":
        hit = next(((n, t) for n, t in named if q.get("tag") in (n, t["name"])), None)
        if not hit:
            return 404, {"error": f"unknown tag {q.get('tag')!r}"}
        n, t = hit
        rows = _samples(st, t, f"{ASOF}T00:00:00Z", f"{ASOF}T23:59:59Z", 100000) or _samples(st, t, "2024-01-01", ASOF, 100000)
        ts, v, g = rows[-1]
        return 200, {"tag": n, "value": v, "timestamp": ts, "quality": "GOOD" if g else "BAD", "unit": t["engunits"]}
    if rest == "alarms":
        k_type, k_tag, k_lvl, k_time = _ALARM_KEYS[slug]
        by_id = {(t["db"], t["tag_id"]): (n, t) for n, t in named}
        out = []
        for db in (HIST, FIELD):
            for a in _db(st, db).execute("SELECT * FROM alarms ORDER BY ts"):
                n, t = by_id[(db, a["tag_id"])]
                out.append({k_type: "ALARM", k_tag: n, k_lvl: "HIGH", k_time: a["ts"].replace(" ", "T"), "Value": a["value"], "Limit": a["limit_value"], "State": a["state"], "Unit": t["engunits"]})
        since = q.get("since")
        if since:
            out = [o for o in out if o[k_time] >= since]
        return 200, {"alarms": sorted(out, key=lambda o: o[k_time])}
    return 404, {"error": "no such endpoint"}


# ------------------------------------------------------------------------------------------------------- EAM / Maximo
_WO_STATUS = {"REL": "APPR", "TECO": "COMP"}
_SR_STATUS = {"M1": "NEW", "M2": "INPROG", "M3": "CLOSED"}


def _where(expr: str | None) -> list[tuple[str, str]]:
    return re.findall(r'spi:(\w+)\s*=\s*"([^"]*)"', expr or "")


def _mx_rows(st, kind: str) -> list[dict]:
    c = _db(st, "sap_pm.sqlite")
    if kind == "mxwo":
        return [{"spi:wonum": r["aufnr"], "spi:description": r["ktext"], "spi:worktype": "CM" if r["auart"] == "PM02" else "PM", "spi:status": _WO_STATUS.get(r["istat"], r["istat"]),
                 "spi:assetnum": str(r["equnr"]) if r["equnr"] else None, "spi:location": r["tplnr"], "spi:schedstart": r["gstrp"], "spi:schedfinish": r["gltrp"], "spi:originatingrecordid": r["qmnum"]} for r in c.execute("SELECT * FROM AUFK")]
    if kind == "mxasset":
        loc = {r["equnr"]: r["tplnr"] for r in c.execute("SELECT equnr, tplnr FROM EQUZ WHERE datbi IS NULL OR datbi >= ?", (ASOF,))}
        return [{"spi:assetnum": str(r["equnr"]), "spi:serialnum": r["sernr"], "spi:manufacturer": r["herst"], "spi:description": r["typbz"], "spi:location": loc.get(r["equnr"]), "spi:installdate": r["baujj"] and str(r["baujj"])} for r in c.execute("SELECT * FROM EQUI")]
    if kind == "mxsr":
        return [{"spi:ticketid": r["qmnum"], "spi:description": r["qmtxt"], "spi:status": _SR_STATUS.get(r["qmart"], r["qmart"]), "spi:assetnum": str(r["equnr"]) if r["equnr"] else None, "spi:location": r["tplnr"], "spi:reportdate": r["qmdat"]} for r in c.execute("SELECT * FROM QMEL")]
    return []


def _infor(st, rest: str, q: dict):
    """Infor EAM: its own names and offset paging (not Maximo's OSLC)."""
    kind = {"workorders": "mxwo", "equipment": "mxasset", "requests": "mxsr"}.get(rest)
    if not kind:
        return 404, {"error": "no such endpoint"}
    rows = [{k.split(":")[1].upper().replace("WONUM", "WORKORDERNUM").replace("ASSETNUM", "EQUIPMENTCODE").replace("TICKETID", "REQUESTNUM"): v for k, v in r.items()} for r in _mx_rows(st, kind)]
    lim, off = int(q.get("limit", 100)), int(q.get("offset", 0))
    return 200, {"Result": {"ResultData": {"Rows": rows[off:off + lim], "TotalRecords": len(rows), "Offset": off}}}


def _eam(st, slug: str, rest: str, q: dict):
    if slug == "eam":
        return _infor(st, rest, q)
    m = re.fullmatch(r"oslc/os/(mxwo|mxasset|mxsr)", rest)
    if not m:
        return 404, {"error": "no such endpoint"}
    rows = _mx_rows(st, m.group(1))
    for k, v in _where(q.get("oslc.where")):
        rows = [r for r in rows if r.get(f"spi:{k}") == v]
    size, page = int(q.get("oslc.pageSize", 100)), int(q.get("pageno", 1))
    body = {"rdfs:member": rows[(page - 1) * size:page * size], "responseInfo": {"totalCount": len(rows), "pagenum": page, "totalPages": -(-len(rows) // size)}}
    if page * size < len(rows):
        qs = urllib.parse.urlencode({**q, "pageno": page + 1})
        body["responseInfo"]["nextPage"] = {"href": f"/v/{slug}/oslc/os/{m.group(1)}?{qs}"}
    return 200, body


# --------------------------------------------------------------------------- vibration condition monitoring and APM
def _spectra(st) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in _db(st, HIST).execute("SELECT * FROM cms_spectra ORDER BY tag, day"):
        out.setdefault(r["tag"], []).append(dict(r))
    return out


def _alerts(st) -> list[dict]:
    """Rule-based alerts over the world's data: the outer-race defect line has doubled since the first reading, or overall vibration is near its alarm."""
    # the near-alarm rule only compares like units: the spectra overall is mm/s, some tags are in other units
    limits = {r["name"]: r["alarm_high"] for r in _db(st, HIST).execute("SELECT name, alarm_high FROM tags WHERE engunits = 'mm/s'")}
    out = []
    for tag, rows in _spectra(st).items():
        first, last = rows[0], rows[-1]
        eq, ms = _split(tag)
        if first["bpfo"] and last["bpfo"] / first["bpfo"] >= 2.0:
            out.append({"machine": eq, "point": tag, "kind": "outer-race defect frequency", "severity": "alert", "since": last["day"], "evidence": f"BPFO amplitude {last['bpfo']} vs {first['bpfo']} at first reading ({last['bpfo'] / first['bpfo']:.1f}x)"})
        lim = limits.get(tag)
        if lim and last["overall"] >= 0.8 * lim:
            out.append({"machine": eq, "point": tag, "kind": "overall vibration near alarm", "severity": "warning", "since": last["day"], "evidence": f"overall {last['overall']} mm/s against alarm {lim}"})
    return out


def _health(st, eq: str) -> dict:
    rows = [r for t, rs in _spectra(st).items() if _split(t)[0] == eq for r in rs[-1:]]
    if not rows:
        return {"score": None, "risk": "unknown", "drivers": []}
    worst = max(rows, key=lambda r: r["overall"])
    alerts = [a for a in _alerts(st) if a["machine"] == eq]
    score = max(0, round(100 - 12 * worst["overall"] - 15 * len(alerts)))
    return {"score": score, "risk": "high" if score < 50 else "medium" if score < 75 else "low", "drivers": [a["evidence"] for a in alerts] or ["no rule fired"]}


_CM_KEYS = {  # machine, point, time, overall, 1x, 2x, bpfo, bpfi, bsf
    "system1": ("Asset", "Point", "Timestamp", "Overall", "1X", "2X", "BPFO", "BPFI", "BSF"),
    "skf_observer": ("Machine", "MeasurementPoint", "MeasDate", "OverallValue", "Order1", "Order2", "BearingOuter", "BearingInner", "BearingBall"),
    "ams": ("Device", "Sensor", "Time", "RMS", "Amp1X", "Amp2X", "OuterRace", "InnerRace", "Ball"),
    "senseye": ("machineId", "sensorId", "time", "overall", "x1", "x2", "bpfo", "bpfi", "bsf"),
    "augury": ("machine", "node", "ts", "vibrationOverall", "f1x", "f2x", "bpfo", "bpfi", "bsf"),
    "ecostruxure": ("asset", "measurement", "at", "value", "h1", "h2", "outer", "inner", "ball"),
    "ft_analytics": ("Device", "Signal", "SampleTime", "Total", "Harm1", "Harm2", "BPFO", "BPFI", "BSF"),
}
_APM_KEYS = {  # asset, health, risk, drivers, alert kind, severity
    "apm": ("asset", "health", "risk", "drivers", "kind", "severity"),
    "ge_apm": ("EntityKey", "HealthIndex", "RiskScore", "Findings", "AlertType", "Priority"),
    "maximo_apm": ("assetnum", "healthscore", "riskrating", "contributors", "alerttype", "severity"),
    "mas_apm": ("assetId", "health", "risk", "contributingFactors", "insight", "criticality"),
    "aspen_mtell": ("Agent", "Score", "Risk", "Reasons", "Warning", "Level"),
    "uptake": ("assetId", "assetHealth", "riskLevel", "insights", "insightType", "severity"),
    "asset_performance": ("assetCode", "performance", "riskBand", "causes", "event", "grade"),
    "asset_intelligence_network": ("assetKey", "score", "band", "signals", "alertClass", "severity"),
    "assetwise": ("ElementId", "ConditionIndex", "RiskClass", "Basis", "Notice", "Priority"),
    "industrial_ai": ("assetRef", "healthScore", "risk", "why", "predictionType", "priority"),
    "forge": ("assetId", "healthScore", "riskCategory", "factors", "alertName", "severity"),
}


def _cm(st, slug: str, rest: str, q: dict):
    k_m, k_p, k_t, k_o, k_1, k_2, k_bo, k_bi, k_bs = _CM_KEYS[slug]
    spectra = _spectra(st)
    machines = sorted({_split(t)[0] for t in spectra})
    if rest in ("machines", ""):
        return 200, {"machines": [{k_m: m, "points": sorted(t for t in spectra if _split(t)[0] == m)} for m in machines]}
    if rest == "measurements":
        wanted = q.get("machine")
        out = [{k_m: _split(t)[0], k_p: t, k_t: f"{r['day']}T00:00:00Z", k_o: r["overall"], k_1: r["f1x"], k_2: r["f2x"], k_bo: r["bpfo"], k_bi: r["bpfi"], k_bs: r["bsf"], "Unit": "mm/s"}
               for t, rs in spectra.items() if not wanted or _split(t)[0] == wanted or t == wanted for r in rs
               if (not q.get("from") or r["day"] >= q["from"][:10]) and (not q.get("to") or r["day"] <= q["to"][:10])]
        return 200, {"measurements": out}
    if rest == "alerts":
        return 200, {"alerts": [{k_m: a["machine"], k_p: a["point"], "Condition": a["kind"], "Severity": a["severity"], "Since": a["since"], "Evidence": a["evidence"]} for a in _alerts(st)]}
    return 404, {"error": "no such endpoint"}


def _apm(st, slug: str, rest: str, q: dict):
    k_a, k_h, k_r, k_d, k_k, k_s = _APM_KEYS[slug]
    machines = sorted({_split(t)[0] for t in _spectra(st)})
    if rest in ("assets", ""):
        return 200, {"assets": [{k_a: m, "site": "CDU1"} for m in machines]}
    m = re.fullmatch(r"assets/([^/]+)/health", rest)
    if m:
        if m.group(1) not in machines:
            return 404, {"error": f"unknown asset {m.group(1)!r}"}
        h = _health(st, m.group(1))
        return 200, {k_a: m.group(1), k_h: h["score"], k_r: h["risk"], k_d: h["drivers"], "asOf": ASOF, "method": "mock rule over vibration data, not a vendor model"}
    if rest == "alerts":
        return 200, {"alerts": [{k_a: a["machine"], k_k: a["kind"], k_s: a["severity"], "raised": a["since"], "evidence": a["evidence"]} for a in _alerts(st)]}
    return 404, {"error": "no such endpoint"}


# --------------------------------------------------------------------------------------------------------- MES / MOM
_MOM_KEYS = {  # work order, product, started, line, lot, material, supplier, test, value, passed
    "opcenter": ("ProductionOrder", "Product", "StartedOn", "WorkCenter", "Batch", "Material", "Vendor", "Characteristic", "Result", "Accepted"),
    "ft_productioncentre": ("OrderNo", "PartNo", "BuildDate", "CellId", "LotNo", "Component", "SupplierCode", "TestName", "Reading", "Pass"),
    "proficy_pa": ("ProcessOrder", "ProductCode", "ActualStart", "ProductionLine", "LotId", "RawMaterial", "SupplierId", "VariableName", "VariableResult", "InSpec"),
    "digital_manufacturing": ("order", "material", "startTime", "workCenter", "batchNumber", "component", "supplier", "inspectionCharacteristic", "value", "accepted"),
}


def _mom(st, slug: str, rest: str, q: dict):
    k_wo, k_pr, k_st, k_ln, k_lot, k_mat, k_sup, k_te, k_va, k_pa = _MOM_KEYS[slug]
    c = _db(st, "kestrel_mes.sqlite")
    lim, off = int(q.get("limit", 200)), int(q.get("offset", 0))
    if rest == "workorders":
        rows = [{k_wo: r["work_order"], "SerialNo": r["serial"], k_pr: r["model"], k_st: r["built"], k_ln: r["line"]} for r in c.execute("SELECT * FROM build_records ORDER BY built, serial")]
    elif rest == "lots":
        rows = [{k_lot: r["lot_id"], k_mat: r["material"], k_sup: r["supplier_code"], "ReceivedOn": r["received"], "PurchaseOrder": r["po_no"], "Quantity": r["qty"]} for r in c.execute("SELECT * FROM lots ORDER BY lot_id")]
    elif rest == "results":
        rows = [{"SerialNo": r["serial"], k_te: r["test_kind"], k_va: r["value"], "Unit": r["unit"], k_pa: bool(r["passed"]), "TestedOn": r["tested"]} for r in c.execute("SELECT * FROM test_records ORDER BY tested, serial")]
    elif rest == "genealogy":
        rows = [{"SerialNo": r["serial"], k_mat: r["component_kind"], k_lot: r["lot_id"]} for r in c.execute("SELECT * FROM genealogy ORDER BY serial")]
    else:
        return 404, {"error": "no such endpoint"}
    for k, v in q.items():
        if k in {"serial", "lot", "work_order"}:
            key = {"serial": "SerialNo", "lot": k_lot, "work_order": k_wo}[k]
            rows = [r for r in rows if r.get(key) == v]
    return 200, {"items": rows[off:off + lim], "total": len(rows), "offset": off}


# ------------------------------------------------------------------------------------------------------- ESP records
def _esp(st, slug: str, rest: str, q: dict):
    if rest == "difa":
        import csv
        with (Path(st.w) / "difa_reports.csv").open(newline="") as f:
            rows = list(csv.DictReader(f))
        return 200, {"reports": rows, "total": len(rows)}
    if rest == "surveillance":
        rows = [dict(r) for r in _db(st, FIELD).execute("SELECT * FROM drive_events ORDER BY ts")]
        if q.get("well"):
            rows = [r for r in rows if r["well"] == q["well"]]
        return 200, {"events": rows, "total": len(rows)}
    return 404, {"error": "no such endpoint"}


# --------------------------------------------------------------------------------------------------------- routing
FAMILIES: dict[str, Callable] = {"historian": _historian, "control": _control, "eam": _eam, "cm": _cm, "apm": _apm, "mom": _mom, "esp": _esp}

PROBES = {"historian": "tags", "control": "tags", "eam": "oslc/os/mxwo", "cm": "alerts", "apm": "alerts", "mom": "lots", "esp": "difa"}


def catalogue() -> dict:
    probe = lambda s, f: "workorders" if s == "eam" else PROBES[f]  # noqa: E731
    return {"systems": [{"slug": s, "name": n, "vendor": v, "family": f, "mirrors": m, "base": f"/v/{s}/", "probe": f"/v/{s}/{probe(s, f)}"} for s, (n, v, f, m) in SYSTEMS.items()],
            "count": len(SYSTEMS), "note": "Mocks over one simulated plant; names and shapes follow each product, data is the world's own."}


def route(st, path: str, q: dict):
    """GET /v/ or /v/<slug>/<rest>; returns (status, body)."""
    parts = path.strip("/").split("/", 2)
    if len(parts) == 1:
        return 200, catalogue()
    slug = parts[1]
    if slug not in SYSTEMS:
        return 404, {"error": f"no mock source named {slug!r}; GET /v/ lists them"}
    rest = parts[2] if len(parts) > 2 else ""
    return FAMILIES[SYSTEMS[slug][2]](st, slug, rest, q)
