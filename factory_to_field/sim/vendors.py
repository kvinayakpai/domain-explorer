"""Mock source systems: six deep mocks, one per product a refinery reliability team is likely to connect, backed by the same simulated plant.

The simulators in server.py cover the systems the agents read today (PI Web API, OPC UA gateway, SAP PM, OSDU, the pump
maker's PLM/MES/QMS, production planning). This module adds six vendor mocks under /v/<slug>/, each with its product's names,
response shapes and paging, and for three of them a session that expires:

  pi_af      PI System / AF (AVEVA)           WebIds, startIndex/maxCount with Links.Next
  deltav     DeltaV (Emerson)                 session, expires after SESSION_REQUESTS requests
  maximo     Maximo (IBM)                     OSLC where and pageno paging
  system1    Bently Nevada System 1           session, opaque nextCursor paging
  ge_apm     APM (GE Vernova)                 session, OData $top/$skip with @odata.nextLink
  esp_difa   ESP surveillance and DIFA        the maker-side teardown feed

35 earlier mocks that were renamed copies of these dialects were retired on 2026-11-08 (see RETIRED and PLAN.md 4.3).
GET /v/ lists the six. The data is the world's own (same tags, alarms, work orders and lots), named the way each product names
it. These are interpretations of each product's API, not vendor-certified, and read-only. The health scores and alerts the
APM mock returns are simple rules over the world's vibration data (see _health), not a vendor's model.
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
# Six deep mocks (session expiry, vendor paging, vendor field names). The other source systems in the taxonomies are
# not mocked: 35 earlier mocks were renamed copies of these dialects and were retired on 2026-11-08 (PLAN.md 4.3).
SYSTEMS: dict[str, tuple[str, str, str, str]] = {
    "pi_af": ("PI System / PI Asset Framework", "AVEVA", "historian", "AF elements and attributes"),
    "deltav": ("DeltaV", "Emerson", "control", "DCS modules"),
    "maximo": ("Maximo", "IBM", "eam", "work orders, assets, service requests"),
    "system1": ("Bently Nevada System 1", "Baker Hughes", "cm", "vibration measurements and alerts"),
    "ge_apm": ("APM (Meridium, SmartSignal)", "GE Vernova", "apm", "asset health and alerts"),
    "esp_difa": ("ESP surveillance and DIFA records", "Baker Hughes / SLB", "esp", "drive events and teardown reports"),
}
RETIRED: dict[str, str] = {
    'proficy_historian': 'Proficy Historian / Plant Applications',
    'aspenone': 'aspenONE',
    'aws_sitewise': 'SiteWise',
    'insights_hub': 'Insights Hub (formerly MindSphere) / Industrial Edge',
    'cognite': 'Cognite Data Fusion',
    'thingworx': 'ThingWorx (IIoT Platform)',
    'openenterprise': 'OpenEnterprise SCADA',
    'experion': 'Experion PKS',
    'centum': 'CENTUM VP',
    'controllogix': 'ControlLogix PLC',
    's7': 'SIMATIC S7 PLC',
    'wincc': 'WinCC',
    'factorytalk': 'FactoryTalk',
    'maximo_eam': 'Maximo EAM',
    'eam': 'EAM',
    'skf_observer': 'SKF @ptitude Observer',
    'ams': 'AMS Machine Works',
    'senseye': 'Senseye Predictive Maintenance',
    'augury': 'Augury Machine Health',
    'ecostruxure': 'EcoStruxure Asset Advisor',
    'ft_analytics': 'FactoryTalk Analytics for Devices',
    'apm': 'APM',
    'maximo_apm': 'Maximo APM',
    'mas_apm': 'Maximo Application Suite — APM',
    'aspen_mtell': 'Aspen Mtell',
    'uptake': 'Uptake APM',
    'asset_performance': 'Asset Performance',
    'asset_intelligence_network': 'Asset Intelligence Network',
    'assetwise': 'AssetWise',
    'industrial_ai': 'Industrial AI Platform',
    'forge': 'Forge for Industrial',
    'opcenter': 'Opcenter Execution',
    'ft_productioncentre': 'FactoryTalk ProductionCentre',
    'proficy_pa': 'Proficy Plant Applications',
    'digital_manufacturing': 'Digital Manufacturing',
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
        return f"\\\\AF\\{t['site']}\\{eq}|{ms}"
    return n


def _hist_point(slug: str, t: dict, native: str) -> dict:
    _eq, ms = _split(t["name"])
    return {"WebId": "F1DP" + _uid("pt", t["name"])[:12], "Path": native, "Name": ms, "DefaultUnitsName": t["engunits"], "DataReferencePlugIn": "PI Point", "PointName": t["name"]}


def _hist_values(slug: str, native: str, t: dict, rows: list[tuple[str, float, bool]]) -> dict:
    return {"Path": native, "Items": [{"Timestamp": ts, "Value": v, "Good": g, "Questionable": not g, "Substituted": False} for ts, v, g in rows]}


def _historian(st, slug: str, rest: str, q: dict):
    tags = _tags(st)
    native = _hist_name(slug)
    if rest in ("tags", ""):
        pat = q.get("filter", "")
        items = [_hist_point(slug, t, native(t)) for t in tags if pat.lower() in (native(t) + t["descriptor"]).lower()]
        size, start = int(q.get("maxCount", 100)), int(q.get("startIndex", 0))
        body: dict = {"Items": items[start:start + size]}
        if start + size < len(items):  # PI Web API style: a Links.Next URL, no total
            body["Links"] = {"Next": f"/v/{slug}/tags?" + urllib.parse.urlencode({**q, "startIndex": start + size, "maxCount": size})}
        return 200, body
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
    return f"{eq}/{ms}/PV"


_ALARM_KEYS = {"deltav": ("EventType", "Module", "Level", "Time")}


def _control(st, slug: str, rest: str, q: dict):
    tags = _tags(st)
    named = [(_ctrl_name(slug, i, t), t) for i, t in enumerate(tags)]
    if rest in ("tags", ""):
        pat = q.get("filter", "").lower()
        items = [{"tag": n, "description": t["descriptor"], "unit": t["engunits"], "area": t["site"]} for n, t in named if pat in (n + t["descriptor"]).lower()]
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


def _eam(st, slug: str, rest: str, q: dict):
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
}
_APM_KEYS = {  # asset, health, risk, drivers, alert kind, severity
    "ge_apm": ("EntityKey", "HealthIndex", "RiskScore", "Findings", "AlertType", "Priority"),
}


def _cursor_page(key: str, rows: list[dict], q: dict) -> dict:
    """Opaque cursor paging: the client cannot compute page 3, it must follow nextCursor."""
    import base64
    size = int(q.get("limit", 50))
    off = int(base64.urlsafe_b64decode(q["cursor"]).decode().split(":")[1]) if q.get("cursor") else 0
    body: dict = {key: rows[off:off + size]}
    if off + size < len(rows):
        body["nextCursor"] = base64.urlsafe_b64encode(f"c:{off + size}".encode()).decode()
    return body


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
        return 200, _cursor_page("measurements", out, q)
    if rest == "alerts":
        return 200, _cursor_page("alerts", [{k_m: a["machine"], k_p: a["point"], "Condition": a["kind"], "Severity": a["severity"], "Since": a["since"], "Evidence": a["evidence"]} for a in _alerts(st)], q)
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
        rows = [{k_a: a["machine"], k_k: a["kind"], k_s: a["severity"], "raised": a["since"], "evidence": a["evidence"]} for a in _alerts(st)]
        top, skip = int(q.get("$top", 50)), int(q.get("$skip", 0))
        body = {"@odata.count": len(rows), "value": rows[skip:skip + top]}
        if skip + top < len(rows):
            body["@odata.nextLink"] = f"/v/{slug}/alerts?" + urllib.parse.urlencode({**q, "$top": top, "$skip": skip + top})
        return 200, body
    return 404, {"error": "no such endpoint"}


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
FAMILIES: dict[str, Callable] = {"historian": _historian, "control": _control, "eam": _eam, "cm": _cm, "apm": _apm, "esp": _esp}

PROBES = {"historian": "tags", "control": "tags", "eam": "oslc/os/mxwo", "cm": "alerts", "apm": "alerts", "esp": "difa"}


def catalogue() -> dict:
    probe = lambda s, f: PROBES[f]  # noqa: E731
    return {"systems": [{"slug": s, "name": n, "vendor": v, "family": f, "mirrors": m, "base": f"/v/{s}/", "probe": f"/v/{s}/{probe(s, f)}"} for s, (n, v, f, m) in SYSTEMS.items()],
            "count": len(SYSTEMS), "note": "Mocks over one simulated plant; names and shapes follow each product, data is the world's own."}


SESSION_SLUGS = {"deltav", "system1", "ge_apm"}  # these want a session first, and the session runs out
SESSION_REQUESTS = 25                           # a session answers this many requests, then 401 session expired


def open_session(st, slug: str) -> tuple[int, dict]:
    """POST /v/<slug>/session. Real products expire sessions; the client must notice the 401 and sign in again."""
    if slug not in SESSION_SLUGS:
        return 404, {"error": f"{slug!r} does not use sessions"}
    sessions = st.__dict__.setdefault("vsessions", {})
    tok = f"{slug}-s{len(sessions) + 1:05d}"
    sessions[tok] = SESSION_REQUESTS
    return 200, {"session": tok, "expires_after_requests": SESSION_REQUESTS, "send_as": "x-session header"}


def route(st, path: str, q: dict):
    """GET /v/ or /v/<slug>/<rest>; returns (status, body)."""
    parts = path.strip("/").split("/", 2)
    if len(parts) == 1:
        return 200, catalogue()
    slug = parts[1]
    if slug not in SYSTEMS:
        return 404, {"error": f"no mock source named {slug!r}; GET /v/ lists them"}
    rest = parts[2] if len(parts) > 2 else ""
    if slug in SESSION_SLUGS:
        sessions = st.__dict__.setdefault("vsessions", {})
        tok = q.pop("_session", "")
        if tok not in sessions or not tok.startswith(slug):
            return 401, {"error": "session required", "hint": f"POST /v/{slug}/session, then send the token in x-session"}
        if sessions[tok] <= 0:
            return 401, {"error": "session expired", "hint": f"POST /v/{slug}/session for a new one"}
        sessions[tok] -= 1
    return FAMILIES[SYSTEMS[slug][2]](st, slug, rest, q)
