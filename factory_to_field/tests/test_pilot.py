"""Pilot readiness without real systems: signed identities, a tamper-evident audit log, the review workflow for
uncertain identity matches, Unified Namespace alarms over MQTT, and a client that copes with how the real systems
behave (tokens, retries, paging, CSRF, data partitions)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime

import pytest
from factory_to_field.agents.agent import Agent
from factory_to_field.agents.drafts import DraftStore
from factory_to_field.agents.sources import HttpSource, SourceError
from factory_to_field.pilot import approvals
from factory_to_field.pilot import idp as idp_mod
from factory_to_field.pilot.audit import AuditLog
from factory_to_field.pilot.connectors import ClientCredentials
from factory_to_field.pilot.review import ReviewStore, apply
from factory_to_field.pilot.uns import run_replay, tag_for_topic
from factory_to_field.sim.server import serve_in_thread

SAP_NOTIF = "/sap/opu/odata/sap/API_MAINTNOTIFICATION/MaintenanceNotification"


@pytest.fixture(scope="module")
def idp():
    srv, url, provider = idp_mod.serve_in_thread()
    yield url, provider
    srv.shutdown()


@pytest.fixture(scope="module")
def strict_sim(world_dir, idp):
    url, provider = idp
    srv, sim_url = serve_in_thread(world_dir, verifier=idp_mod.JwksVerifier(url, provider.issuer), require_identity=True, odata_page_size=7)
    yield sim_url
    srv.shutdown()


def _token(provider, user):
    return provider.login(user, idp_mod.DIRECTORY[user].password)


# ------------------------------------------------------------------------------------------------ audit log
def test_audit_log_chain_detects_tampering(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    for i in range(3):
        log.append("A. Rao", "maintenance_planner", "approve", f"DRAFT-{i:04d}", {"n": i})
    assert AuditLog(path).verify() == (True, None)          # survives a restart
    lines = path.read_text().splitlines()
    rec = json.loads(lines[1])
    rec["actor"] = "Someone Else"                           # rewrite history
    lines[1] = json.dumps(rec, sort_keys=True)
    path.write_text("\n".join(lines) + "\n")
    assert AuditLog(path).verify() == (False, 2)


# ------------------------------------------------------------------------------------------------ identity
def test_identity_provider_signs_and_refuses(idp):
    _url, provider = idp
    claims = provider.verify(_token(provider, "a.rao"))
    assert claims["name"] == "A. Rao" and claims["roles"] == ["maintenance_planner"]
    with pytest.raises(PermissionError):
        provider.login("a.rao", "wrong")
    with pytest.raises(PermissionError):
        provider.client_credentials("ftf-agent", idp_mod.CLIENTS["ftf-agent"]["secret"], scope="drafts.decide")
    expired = idp_mod.IdentityProvider(issuer=provider.issuer, ttl_s=-120)
    with pytest.raises(PermissionError, match="expired"):
        expired.verify(expired.login("a.rao", "demo-a.rao"))
    other = idp_mod.IdentityProvider(issuer=provider.issuer)
    with pytest.raises(PermissionError):                    # signed by a key the provider never published
        provider.verify(other.login("a.rao", "demo-a.rao"))


def test_approvals_need_the_right_signed_identity_and_the_systems_check_it_again(idp, strict_sim):
    url, provider = idp
    store, audit = DraftStore(), AuditLog(None)
    d = store.create("sap_pm.notification", "Bearing fault P-101A", {"functional_location": "CDU1-10-P-101A"}, "evidence-backed",
                     ["kg:x"], datetime(2026, 10, 17))
    with pytest.raises(PermissionError, match="maintenance_planner"):
        approvals.approve(store, d.id, _token(provider, "m.das"), provider.verify, audit)
    approvals.approve(store, d.id, _token(provider, "a.rao"), provider.verify, audit)
    assert d.status == "approved" and d.decided_by == "A. Rao"
    writer = HttpSource(strict_sim, token="none")
    rec = approvals.release(store, d.id, writer, _token(provider, "a.rao"), provider.verify, audit)
    assert rec["approved_by"] == "A. Rao (maintenance_planner)" and rec["subject"] == "a.rao"
    actions = [r["action"] for r in audit.records()]
    assert actions == ["approve_refused", "approve", "release"] and audit.verify() == (True, None)
    # the static release token and a signed person without the role are both refused by the system itself
    with pytest.raises(SourceError, match="signed approver identity"):
        writer.post(SAP_NOTIF, {"x": 1}, token="release", headers={"X-Approved-By": "anyone", "X-Draft-Id": d.id})
    with pytest.raises(SourceError, match="does not hold the maintenance_planner role"):
        writer.post(SAP_NOTIF, {"x": 1}, token=_token(provider, "m.das"), headers={"X-Draft-Id": d.id})


# ------------------------------------------------------------------------------------------------ connectors
def test_agent_reads_with_oauth2_client_credentials_and_refreshes(idp, strict_sim):
    url, _provider = idp
    cred = ClientCredentials(f"{url}/oauth2/token", "ftf-agent", idp_mod.CLIENTS["ftf-agent"]["secret"])
    src = HttpSource(strict_sim, token=cred)
    assert src.point("10P101A.VIB_DE")["alarm_high"] == 4.5
    cred._token = cred.token()[:-4] + "AAAA"                 # a token the systems no longer accept
    assert src.point("A07_MTR_T")["alarm_high"] == 135.0    # 401, refresh once, retry
    assert cred.fetches == 2
    with pytest.raises(SourceError, match="read-only"):
        src.post(SAP_NOTIF, {"x": 1}, headers={"X-Draft-Id": "DRAFT-9999"})


def test_paging_retries_csrf_and_partitions(idp, strict_sim, world_dir):
    url, _provider = idp
    cred = ClientCredentials(f"{url}/oauth2/token", "ftf-agent", idp_mod.CLIENTS["ftf-agent"]["secret"])
    src = HttpSource(strict_sim, token=cred, backoff_s=0.01)
    _srv, plain = serve_in_thread(world_dir)
    full = HttpSource(plain).get(SAP_NOTIF)["d"]["results"]
    paged = src.get(SAP_NOTIF)["d"]["results"]                # server pages of 7 rows, followed via __next
    assert len(full) > 7 and [r["MaintenanceNotification"] for r in paged] == [r["MaintenanceNotification"] for r in full]
    pts = src.get("/piwebapi/points", nameFilter="10P10*", maxCount=3)["Items"]
    assert len(pts) > 3 and len(pts) == len(HttpSource(plain).get("/piwebapi/points", nameFilter="10P10*")["Items"])
    urllib.request.urlopen(urllib.request.Request(f"{strict_sim}/sim/faults", data=json.dumps({"rate_limit_every": 2}).encode(), method="POST"))
    try:
        for tag in ("10P101A.VIB_DE", "A07_MTR_T", "10P101B.VIB_DE"):
            assert src.point(tag) is not None
        assert src.retried > 0
    finally:
        urllib.request.urlopen(urllib.request.Request(f"{strict_sim}/sim/faults", data=b"{}", method="POST"))
    raw = urllib.request.Request(f"{strict_sim}/osdu/api/storage/v2/records/x", headers={"Authorization": f"Bearer {cred.token()}"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(raw)
    assert e.value.code == 400                                # no data-partition-id
    assert src.post("/osdu/api/search/v2/query", {"query": 'data.FacilityName:"Well A-07"', "limit": 1})["totalCount"] == 1
    no_csrf = urllib.request.Request(f"{strict_sim}{SAP_NOTIF}", data=b"{}", method="POST",
                                     headers={"Authorization": f"Bearer {cred.token()}", "Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(no_csrf)
    assert e.value.code == 403 and e.value.headers.get("x-csrf-token") == "Required"


# ------------------------------------------------------------------------------------------------ review workflow
def test_review_workflow_decides_and_shrinks_the_queue(idp, kg_dir, world_dir, tmp_path):
    _url, provider = idp
    store, audit = ReviewStore(":memory:"), AuditLog(None)
    queue = kg_dir / "review_queue.json"
    items = [x for x in store.queue(queue) if x["status"] == "open"]
    assert items, "the KG build leaves uncertain links for review"
    with pytest.raises(PermissionError, match="data_steward"):
        store.decide(items[0]["id"], _token(provider, "a.rao"), provider.verify, audit, dismiss="retired")
    truth = {tuple(r[:3]): r[3] for r in json.loads((world_dir / "truth.json").read_text())}
    tok = _token(provider, "p.kulkarni")
    for it in items:
        store.open(it["id"], tok, provider.verify)
        canon = truth.get((it["system"], it["table"], it["key"]))
        if canon:
            store.decide(it["id"], tok, provider.verify, audit, link=canon)
        else:
            store.decide(it["id"], tok, provider.verify, audit, dismiss="tag retired; not an asset")
    m = store.metrics(queue)
    assert m["open"] == 0 and m["decided"] == len(items) and m["median_seconds_per_decision"] is not None
    after = apply(store, world_dir, tmp_path / "kg_reviewed", skip_shacl=True)
    assert after["review_queue"] == 0 and after["review_dismissed"] == m["dismissed"]
    assert after["resolution"]["precision"] >= 0.98
    assert [r["action"] for r in audit.records()].count("review_decide") == len(items)


# ------------------------------------------------------------------------------------------------ UNS over MQTT
def test_uns_topics_map_to_tags():
    assert tag_for_topic("aurelia/r1/cdu1/10-p-101a/vibration_de") == "10P101A.VIB_DE"
    assert tag_for_topic("aurelia/fa/p3/a-07-esp/motor_temperature") == "A07_MTR_T"
    assert tag_for_topic("other/r1/x/y/z") is None


def test_uns_replay_over_mqtt_opens_cases_for_both_alarms(world_dir, kg):
    _srv, url = serve_in_thread(world_dir)
    src = HttpSource(url)
    opened, sent = run_replay(Agent(kg=kg, src=src), src, world_dir / "uns_replay.jsonl")
    assert sent > 100
    by_tag = {o.tag: o for o in opened}
    assert set(by_tag) == {"10P101A.VIB_DE", "A07_MTR_T"}
    assert by_tag["10P101A.VIB_DE"].limit == 4.5 and by_tag["10P101A.VIB_DE"].value > 4.5
    assert "B-24-117" in by_tag["10P101A.VIB_DE"].summary
    assert by_tag["A07_MTR_T"].answer.get("elastomer_lot") in ("E-25-031", "lot:E-25-031")
    assert all(o.drafts for o in opened)                     # drafts only: nothing was written
