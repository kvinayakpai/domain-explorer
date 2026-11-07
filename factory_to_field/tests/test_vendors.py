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


@pytest.fixture(scope="module")
def sim(world_dir):
    srv, url = serve_in_thread(world_dir)
    yield url
    srv.shutdown()


def get(base: str, path: str, token: str | None = "ro-agent"):
    req = urllib.request.Request(base + path, headers={"Authorization": f"Bearer {token}"} if token else {})
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


def test_every_named_source_system_has_a_mock():
    named: set[str] = set()
    for sub in TAXONOMIES:
        d = yaml.safe_load((REPO / "data" / "taxonomy" / f"{sub}.yaml").read_text())
        named |= {s["product"] for s in d["sourceSystems"]}
    mocked = {name for name, *_ in vendors.SYSTEMS.values()}
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())  # noqa: E731  ('Maximo Application Suite — APM' vs '... - APM')
    missing = {n for n in named - COVERED if norm(n) not in {norm(m) for m in mocked}}
    assert not missing, f"source systems named in the taxonomies with no mock: {sorted(missing)}"
    assert len(vendors.SYSTEMS) == 41


def test_each_mock_answers_with_data_and_needs_a_token(sim):
    code, cat = get(sim, "/v/")
    assert code == 200 and cat["count"] == 41
    for s in cat["systems"]:
        code, body = get(sim, s["probe"])
        assert code == 200 and first_list(body), f"{s['slug']} returned nothing at {s['probe']}"
        assert get(sim, s["probe"], token=None)[0] == 401
    assert get(sim, "/v/no_such_system/tags")[0] == 404


def test_historians_return_the_world_values_in_their_own_shape(sim, world_dir):
    files = FileSource(world_dir)
    n = "10P101A.VIB_DE"
    want = [r["value"] for r in files.raw(n, "2026-10-16 00:00:00Z", "2026-10-16 02:00:00Z")]
    assert len(want) > 10
    rng = "start=2026-10-16T00:00:00Z&end=2026-10-16T02:00:00Z&max=1000"
    code, b = get(sim, f"/v/proficy_historian/history?tag=CDU1.P101A.VIB_DE&{rng}")
    assert [s["Value"] for s in b["Data"]["Tag"]["Samples"]] == want
    _, b = get(sim, f"/v/aws_sitewise/history?tag=/CDU1/P101A/vib_de&{rng}")
    assert [x["value"]["doubleValue"] for x in b["assetPropertyValueHistory"]] == want
    _, b = get(sim, f"/v/cognite/history?tag=pi:{n}&{rng}")
    assert [d["value"] for d in b["items"][0]["datapoints"]] == want
    _, b = get(sim, f"/v/thingworx/history?tag=P101A.VIB_DE&{rng}")
    assert [r["value"] for r in b["rows"]] == want
    _, b = get(sim, f"/v/aspenone/history?tag=P101A_VIB_DE&{rng}")
    assert [s["x"] for s in b["data"][0]["samples"]] == want
    assert get(sim, f"/v/cognite/history?tag=nope&{rng}")[0] == 404


def test_field_scada_mock_serves_the_field_tags_only(sim):
    _, b = get(sim, "/v/openenterprise/tags?limit=1000")
    names = [t["name"] for t in b["items"]]
    assert names and all(re.match(r"^[A-Z]\d+:", x) for x in names)


def test_control_systems_name_the_same_point_differently_and_agree_on_alarms(sim):
    seen = {}
    for slug in ("deltav", "experion", "centum", "controllogix", "wincc", "factorytalk"):
        _, b = get(sim, f"/v/{slug}/tags?filter=P101A&limit=50")
        seen[slug] = {t["tag"] for t in b["tags"] if "VIB" in t["tag"].upper() and ("DE" in t["tag"].upper())}
    assert len({frozenset(v) for v in seen.values()}) == len(seen), "each product should name the tag its own way"
    code, one = get(sim, "/v/deltav/read?tag=P101A/VIB_DE/PV")
    assert code == 200 and one["unit"] == "mm/s"
    counts = {slug: len(get(sim, f"/v/{slug}/alarms")[1]["alarms"]) for slug in ("deltav", "experion", "centum", "s7")}
    assert len(set(counts.values())) == 1 and counts["deltav"] == 24  # 21 refinery + 3 field alarms
    _, dv = get(sim, "/v/deltav/alarms?since=2026-10-16T00:00:00Z")
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
    assert get(sim, "/v/maximo_eam/oslc/os/mxasset")[1]["responseInfo"]["totalCount"] == 346
    _, inf = get(sim, "/v/eam/workorders?limit=5")  # Infor EAM names the same orders its own way
    assert inf["Result"]["ResultData"]["TotalRecords"] == total and "WORKORDERNUM" in inf["Result"]["ResultData"]["Rows"][0]


def test_condition_monitoring_systems_agree_on_the_planted_bearing_fault(sim):
    for slug, k_machine in (("system1", "Asset"), ("skf_observer", "Machine"), ("ams", "Device"), ("augury", "machine")):
        _, b = get(sim, f"/v/{slug}/alerts")
        hits = [a for a in b["alerts"] if a[k_machine] == "P101A" and "outer-race" in a["Condition"]]
        assert hits and "53.5x" in hits[0]["Evidence"], slug
    _, b = get(sim, "/v/system1/measurements?machine=P101A&from=2026-10-01")
    assert b["measurements"] and {"Overall", "BPFO", "1X"} <= set(b["measurements"][0])


def test_apm_health_ranks_the_failing_pump_worst_and_says_it_is_a_mock(sim):
    _, bad = get(sim, "/v/ge_apm/assets/P101A/health")
    _, ok = get(sim, "/v/ge_apm/assets/P102A/health")
    assert bad["HealthIndex"] < ok["HealthIndex"] and bad["RiskScore"] == "high"
    assert "not a vendor model" in bad["method"]
    assert get(sim, "/v/uptake/assets/NOPE/health")[0] == 404


def test_mom_systems_hold_the_same_lots_under_different_field_names(sim):
    _, a = get(sim, "/v/opcenter/lots?limit=1000")
    _, b = get(sim, "/v/proficy_pa/lots?limit=1000")
    assert a["total"] == b["total"] == 280
    assert {x["Batch"] for x in a["items"]} == {x["LotId"] for x in b["items"]}
    _, g = get(sim, "/v/ft_productioncentre/genealogy?serial=OEM-24-0398")
    assert g["items"] and all(r["SerialNo"] == "OEM-24-0398" for r in g["items"])


def test_esp_records(sim):
    _, d = get(sim, "/v/esp_difa/difa")
    assert d["total"] >= 1 and d["reports"][0]["difa_no"].startswith("DIFA-")
    _, s = get(sim, "/v/esp_difa/surveillance?well=A-01")
    assert s["events"] and all(e["well"] == "A-01" for e in s["events"])
