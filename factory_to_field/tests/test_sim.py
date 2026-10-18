from __future__ import annotations

import pytest
from factory_to_field.agents import gold, tools
from factory_to_field.agents.agent import Agent
from factory_to_field.agents.drafts import DraftStore
from factory_to_field.agents.release import release
from factory_to_field.agents.sources import FileSource, HttpSource, SourceError
from factory_to_field.sim.server import odata_filter, serve_in_thread


@pytest.fixture(scope="module")
def sim(world_dir):
    srv, url = serve_in_thread(world_dir)
    yield url
    srv.shutdown()


@pytest.fixture(scope="module")
def http(sim):
    return HttpSource(sim)


@pytest.fixture(scope="module")
def files(world_dir):
    return FileSource(world_dir)


def test_every_system_answers_the_same_over_http_as_from_files(http, files):
    n = "10P101A.VIB_DE"
    assert http.point(n) == files.point(n) and http.point("30P301A_VIB_DE") == files.point("30P301A_VIB_DE") and http.point("A07_MTR_T") == files.point("A07_MTR_T")
    assert http.point("no.such.tag") is None
    assert http.daily(n, "2026-09-17", "2026-10-16") == [{**r, "n_good": None} for r in files.daily(n, "2026-09-17", "2026-10-16")]
    assert len(http.raw(n, "2026-10-16 00:00:00Z", "2026-10-16 07:30:00Z")) == len(files.raw(n, "2026-10-16 00:00:00Z", "2026-10-16 07:30:00Z"))
    assert http.alarms(n, "2026-10-17 00:00:00Z") == files.alarms(n, "2026-10-17 00:00:00Z")
    assert http.spectra(n, "2026-10-15", limit=5) == files.spectra(n, "2026-10-15", limit=5)
    assert http.notifications("P-101B", "2026-10-17", 5) == files.notifications("P-101B", "2026-10-17", 5)
    assert http.flocs("P-101A") == files.flocs("P-101A") and http.stock("Bearing set, BB2-650", "R1") == files.stock("Bearing set, BB2-650", "R1")
    assert http.windows("R1", "2026-10-17") == files.windows("R1", "2026-10-17") and http.rigs() == files.rigs()
    assert http.allocation("A-07", "2026-10-17") == files.allocation("A-07", "2026-10-17")
    assert http.lot_change("E-25-031") == files.lot_change("E-25-031") and http.lot_tests("B-24-117", "press_fit_force") == files.lot_tests("B-24-117", "press_fit_force")
    assert http.difa("A-04", "2026-10-17") == files.difa("A-04", "2026-10-17") and http.well_master("A-04") == files.well_master("A-04")


def test_odata_dialect(http):
    r = http.get("/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification", **{"$filter": "endswith(FunctionalLocation,'P-101B') and NotificationDate ge '2026-09-01'", "$orderby": "NotificationDate desc", "$top": 2})
    rows = r["d"]["results"]
    assert len(rows) == 2 and rows[0]["NotificationDate"] >= rows[1]["NotificationDate"] and all(x["FunctionalLocation"].endswith("P-101B") for x in rows)
    assert odata_filter([{"a": "x"}, {"a": "y"}], "a eq 'y'") == [{"a": "y"}]
    with pytest.raises(ValueError):
        odata_filter([], "a in ('x')")


def test_credentials_and_read_only(sim):
    with pytest.raises(SourceError) as e:
        HttpSource(sim, token="bad").get("/prod/api/rigs")
    assert "401" in str(e.value)
    ro = HttpSource(sim)
    with pytest.raises(SourceError) as e:
        ro.post("/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification", {"x": 1})
    assert "403" in str(e.value)
    with pytest.raises(SourceError) as e:  # even the release credential cannot write to PI or SCADA
        ro.post("/piwebapi/streams/F1DP000001/value", {"Value": 40}, token="release")
    assert "403" in str(e.value) and "read-only" in str(e.value)
    with pytest.raises(SourceError) as e:  # release credential without an approver and draft id
        ro.post("/qms/api/claims", {"x": 1}, token="release")
    assert "X-Approved-By" in str(e.value)


def test_only_approved_drafts_are_released(sim):
    from factory_to_field.agents.core import parse_ts
    st = DraftStore()
    d = st.create("qms.warranty_claim", "claim", {"lot": "B-24-117"}, "r", ["kg:x"], parse_ts("2026-10-17T06:00:00Z"))
    admin = HttpSource(sim, token="release")
    with pytest.raises(PermissionError):
        release(st, d.id, admin)
    st.approve(d.id, "M. Das", "quality_engineer")
    rec = release(st, d.id, admin)
    assert rec["approved_by"].startswith("M. Das") and st.items[d.id].status == "released"
    assert any(w["id"] == rec["id"] for w in HttpSource(sim).get("/sim/writes")["writes"])


def test_gold_cases_pass_through_the_simulators(sim, http, kg, world_dir):
    r = gold.score(Agent(kg=kg, world=world_dir, src=http), world_dir)
    bad = [(c["case"], [k for k, v in c["checks"].items() if not v], c["problems"]) for c in r["cases"] if not c["ok"]]
    assert not bad, bad
    assert tools.STORE.items is not None
