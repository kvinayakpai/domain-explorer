"""The mock source systems (sim/vendors.py): every system the taxonomies name answers, in its own dialect, from the same world."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml
from factory_to_field.agents.sources import FileSource
from factory_to_field.sim import vendors
from factory_to_field.sim.server import serve_in_thread

REPO = Path(__file__).resolve().parents[2]
TAXONOMIES = ("refinery_operations", "upstream_artificial_lift", "predictive_maintenance", "mes_quality", "asset_health_monitoring", "maintenance", "shop_floor_iot")
# systems the original simulators already cover, so they need no mock under /v/
COVERED = {"PI System", "S/4HANA Asset Management (PM)", "PM/EAM", "OSDU Data Platform (well master data)"}


def login(base: str, slug: str) -> str:
    req = urllib.request.Request(f"{base}/v/{slug}/session", data=b"{}", method="POST", headers={"Authorization": "Bearer ro-agent", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["session"]


@pytest.fixture(scope="module")
def sim(world_dir):
    srv, url = serve_in_thread(world_dir)
    yield url
    srv.shutdown()


def get(base: str, path: str, token: str | None = "ro-agent", session: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if session:
        headers["x-session"] = session
    req = urllib.request.Request(base + path, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def first_list(body) -> list:
    if isinstance(body, list):
        return body
    for v in body.values() if isinstance(body, dict) else []:
        found = first_list(v)
        if found:
            return found
    return []


def test_taxonomy_names_are_mocked_retired_or_covered():
    named: set[str] = set()
    for sub in TAXONOMIES:
        d = yaml.safe_load((REPO / "data" / "taxonomy" / f"{sub}.yaml").read_text())
        named |= {s["product"] for s in d["sourceSystems"]}
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731  ('Maximo Application Suite — APM' vs '... - APM')
    mocked = {norm(name) for name, *_ in vendors.SYSTEMS.values()}
    retired = {norm(n) for n in vendors.RETIRED.values()}
    missing = {n for n in named - COVERED if norm(n) not in mocked | retired}
    assert not missing, f"source systems named in the taxonomies that are neither mocked nor on the retired list: {sorted(missing)}"
    assert len(vendors.SYSTEMS) == 6 and len(vendors.RETIRED) == 35 and not set(vendors.SYSTEMS) & set(vendors.RETIRED)


def test_each_mock_answers_with_data_and_needs_a_token(sim):
    code, cat = get(sim, "/v/")
    assert code == 200 and cat["count"] == 6
    for s in cat["systems"]:
        sess = login(sim, s["slug"]) if s["slug"] in vendors.SESSION_SLUGS else None
        code, body = get(sim, s["probe"], session=sess)
        assert code == 200 and first_list(body), f"{s['slug']} returned nothing at {s['probe']}"
        assert get(sim, s["probe"], token=None, session=sess)[0] == 401
    assert get(sim, "/v/no_such_system/tags")[0] == 404
    assert get(sim, "/v/cognite/tags")[0] == 404  # a retired mock is gone, not hidden


def test_sessions_are_required_and_expire(sim):
    assert get(sim, "/v/deltav/tags?limit=1")[0] == 401  # no session at all
    tok = login(sim, "deltav")
    codes = [get(sim, "/v/deltav/tags?limit=1", session=tok)[0] for _ in range(vendors.SESSION_REQUESTS + 1)]
    assert codes[:-1] == [200] * vendors.SESSION_REQUESTS and codes[-1] == 401
    code, body = get(sim, "/v/deltav/tags?limit=1", session=tok)
    assert code == 401 and body["error"] == "session expired"
    assert get(sim, "/v/deltav/tags?limit=1", session=login(sim, "deltav"))[0] == 200
    assert get(sim, "/v/system1/alerts", session=tok)[0] == 401  # a session is for one product only


def test_pi_af_history_matches_the_world_and_pages_by_link(sim, world_dir):
    files = FileSource(world_dir)
    n = "10P101A.VIB_DE"
    want = [r["value"] for r in files.raw(n, "2026-10-16 00:00:00Z", "2026-10-16 02:00:00Z")]
    assert len(want) > 10
    rng = "start=2026-10-16T00:00:00Z&end=2026-10-16T02:00:00Z&max=1000"
    code, b = get(sim, f"/v/pi_af/history?tag=%5C%5CAF%5CCDU1%5CP101A%7CVIB_DE&{rng}")
    assert code == 200 and [s["Value"] for s in b["Items"]] == want
    assert get(sim, f"/v/pi_af/history?tag=nope&{rng}")[0] == 404
    got, path = [], "/v/pi_af/tags?maxCount=100"
    while path:
        _, b = get(sim, path)
        got += b["Items"]
        path = b.get("Links", {}).get("Next")
    _, everything = get(sim, "/v/pi_af/tags?maxCount=100000")
    assert len(got) == len(everything["Items"]) > 100 and len({x["WebId"] for x in got}) == len(got)


def test_deltav_names_points_its_own_way_and_has_all_the_alarms(sim, world_dir):
    import sqlite3
    tok = login(sim, "deltav")
    _, b = get(sim, "/v/deltav/tags?filter=P101A&limit=50", session=tok)
    assert any(t["tag"] == "P101A/VIB_DE/PV" for t in b["tags"])
    code, one = get(sim, "/v/deltav/read?tag=P101A/VIB_DE/PV", session=tok)
    assert code == 200 and one["unit"] == "mm/s"
    _, al = get(sim, "/v/deltav/alarms", session=tok)
    want = sum(sqlite3.connect(world_dir / f"{db}.sqlite").execute("SELECT COUNT(*) FROM alarms").fetchone()[0] for db in ("historian_pi", "scada_fielda"))
    assert len(al["alarms"]) == want > 24  # every alarm the world holds, refinery and field
    _, dv = get(sim, "/v/deltav/alarms?since=2026-10-16T00:00:00Z", session=tok)
    assert any("P101A" in a["Module"] and a["Time"].startswith("2026-10-16") for a in dv["alarms"])


def test_maximo_pages_work_orders_and_filters_by_status(sim, world_dir):
    import sqlite3
    total = sqlite3.connect(world_dir / "sap_pm.sqlite").execute("SELECT COUNT(*) FROM AUFK").fetchone()[0]
    got, path, pages = [], "/v/maximo/oslc/os/mxwo?oslc.pageSize=200", 0
    while path:
        _, b = get(sim, path)
        got += b["rdfs:member"]
        path = b["responseInfo"].get("nextPage", {}).get("href")
        pages += 1
    assert len(got) == total and pages == -(-total // 200) and len({w["spi:wonum"] for w in got}) == total
    _, b = get(sim, '/v/maximo/oslc/os/mxwo?oslc.where=spi:status="COMP"&oslc.pageSize=1000')
    assert b["responseInfo"]["totalCount"] == sum(1 for w in got if w["spi:status"] == "COMP") > 0
    assert get(sim, "/v/maximo/oslc/os/mxasset")[1]["responseInfo"]["totalCount"] == 346


def test_system1_follows_cursors_and_flags_the_planted_bearing_fault(sim):
    tok = login(sim, "system1")
    _, whole = get(sim, "/v/system1/measurements?machine=P101A&limit=100000", session=tok)
    got, path = [], "/v/system1/measurements?machine=P101A&limit=10"
    while path:
        _, b = get(sim, path, session=tok)
        got += b["measurements"]
        path = f"/v/system1/measurements?machine=P101A&limit=10&cursor={b['nextCursor']}" if b.get("nextCursor") else None
    assert got == whole["measurements"] and len(got) > 20 and {"Overall", "BPFO", "1X"} <= set(got[0])
    _, a = get(sim, "/v/system1/alerts", session=tok)
    hits = [x for x in a["alerts"] if x["Asset"] == "P101A" and "outer-race" in x["Condition"]]
    assert hits and "53.5x" in hits[0]["Evidence"]


def test_ge_apm_pages_with_odata_ranks_the_failing_pump_worst_and_says_it_is_a_mock(sim):
    tok = login(sim, "ge_apm")
    _, bad = get(sim, "/v/ge_apm/assets/P101A/health", session=tok)
    _, ok = get(sim, "/v/ge_apm/assets/P102A/health", session=tok)
    assert bad["HealthIndex"] < ok["HealthIndex"] and bad["RiskScore"] == "high"
    assert "not a vendor model" in bad["method"]
    assert get(sim, "/v/ge_apm/assets/NOPE/health", session=tok)[0] == 404
    got, path = [], "/v/ge_apm/alerts?$top=1"
    while path:
        _, b = get(sim, path, session=tok)
        got += b["value"]
        path = b.get("@odata.nextLink")
    _, all_ = get(sim, "/v/ge_apm/alerts?$top=1000", session=tok)
    assert got == all_["value"] and b["@odata.count"] == len(got) >= 2


def test_esp_records(sim):
    _, d = get(sim, "/v/esp_difa/difa")
    assert d["total"] >= 1 and d["reports"][0]["difa_no"].startswith("DIFA-")
    _, s = get(sim, "/v/esp_difa/surveillance?well=A-01")
    assert s["events"] and all(e["well"] == "A-01" for e in s["events"])


def test_vendor_source_reads_work_orders_and_difa_through_the_mocks_and_agrees_with_files(world_dir):
    """Plan 2.3: the same questions asked through Maximo (OSLC paging) and the ESP/DIFA mock give the file source's answers."""
    from factory_to_field.agents.sources import VendorSource
    srv, base = serve_in_thread(world_dir)
    try:
        files, via = FileSource(world_dir), VendorSource(base)
        flocs = files.flocs("")
        assert len(flocs) > 5
        for day in ("2026-10-17", "2026-06-01"):
            f = sorted((o["aufnr"], o["istat"], o["gstrp"]) for o in files.open_orders(flocs, day))
            v = sorted((o["aufnr"], o["istat"], o["gstrp"]) for o in via.open_orders(flocs, day))
            assert f == v, day
        assert [r["difa_no"] for r in files.difa(None, "2026-10-17")] == [r["difa_no"] for r in via.difa(None, "2026-10-17")]
        assert [r["difa_no"] for r in files.difa("A-01", "2026-10-17")] == [r["difa_no"] for r in via.difa("A-01", "2026-10-17")]
    finally:
        srv.shutdown()
