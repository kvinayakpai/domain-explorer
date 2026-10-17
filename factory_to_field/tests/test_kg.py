from __future__ import annotations

import json
from datetime import date

from factory_to_field.kg import shapes
from factory_to_field.kg.build import build_kg
from factory_to_field.kg.store import run_life_groups


def test_gate_recall_precision_and_shacl(metrics):
    r = metrics["resolution"]
    assert r["recall"] >= 0.95 and r["precision"] >= 0.98, r
    assert metrics["shacl"]["conforms"] is True, metrics["shacl"].get("report")
    assert metrics["gate_passed"]


def test_shacl_has_teeth():
    from rdflib import Graph
    bad = Graph()
    bad.parse(data="""@prefix ftf: <https://domain-explorer.dev/ftf#> .
    <urn:x:fe1> a ftf:FailureEvent ; ftf:id "fe1" ; ftf:label "x" ; ftf:occurred_on "2026-01-01"^^<http://www.w3.org/2001/XMLSchema#date> .""", format="turtle")
    ok, text, _ = shapes.validate_graph(bad)
    assert not ok and "mode" in text


def test_position_vs_unit_distinction(kg):
    # who was in P-101A on 1 March, and who is there now
    assert kg.unit_at("pos:R1:10-P-101A", date(2026, 3, 1))["serial"] == "OEM-24-0412"
    assert kg.unit_at("pos:R1:10-P-101A", date(2026, 10, 16))["serial"] == "OEM-25-1187"
    # the 8 March failure belongs to the unit and to the position it was at *then*
    f_a = kg.failures_at("pos:R1:10-P-101A")
    assert [(x["serial"], x["mode"], x["on"]) for x in f_a if x["on"].year == 2026] == [("OEM-24-0412", "VIB", date(2026, 3, 8))]
    f_b = kg.failures_at("pos:R1:10-P-101B")
    assert [(x["serial"], x["mode"], x["on"]) for x in f_b if x["on"].year == 2026] == [("OEM-24-0412", "ELP", date(2026, 9, 21))]
    # unit trace: one unit, two positions, one failure at each
    tr = [r for r in kg.unit_trace("unit:OEM-24-0412") if r["mode"]]
    assert {(r["pos"], r["mode"]) for r in tr} == {("pos:R1:10-P-101A", "VIB"), ("pos:R1:10-P-101B", "ELP")}


def test_time_travel_agrees_with_the_world(kg, world):
    import random
    rnd = random.Random(1)
    pos = [p for p, v in world.positions.items() if v["kind"] in ("pump", "esp_position")]
    ok = tot = 0
    for p in rnd.sample(pos, 60):
        on = date(2024, 1, 1) + (date(2026, 10, 1) - date(2024, 1, 1)) * rnd.random()
        on = date.fromordinal(int(on.toordinal()))
        want = world.unit_at(p, on)
        got = kg.unit_at(p, on)
        tot += 1
        ok += (got is None and want is None) or (got is not None and want is not None and got["unit"] == want)
    assert ok / tot >= 0.95, (ok, tot)


def test_lot_exposure_and_waived_changes(kg):
    assert kg.cq("cq06", lot=kg.node("lot:B-24-117")) == [{"units": 38, "customers": 9}]
    assert kg.cq("cq06", lot=kg.node("lot:E-25-031")) == [{"units": 61, "customers": 4}]
    lots = {r["lot"] for r in kg.cq("cq05")}
    assert {"lot:B-24-117", "lot:E-25-031"} <= lots
    assert [r["eco"] for r in kg.cq("cq11")] == ["eco:ECO-24-1147", "eco:ECO-25-0112", "eco:ECO-25-0389", "eco:ECO-26-0057"]


def test_run_life_by_seal_build_window(kg):
    g = run_life_groups(kg, date(2025, 8, 1))
    assert (g["since"]["n"], g["since"]["failed"], g["since"]["running"]) == (12, 7, 5)
    assert g["since"]["km_median_days"] == 290 and g["before"]["km_median_days"] == 780
    # the same string averaged under the well would hide the early failure: A-07 has three runs, only the last is new
    a07 = [r for r in g["members"]["before"] + g["members"]["since"] if r["well"].startswith("A-07")]
    assert len(a07) == 3


def test_crosswalk_resolves_messy_names(kg):
    rows = kg.cq("cq10", system="SAP-PM", value="OEM 24 0398")
    assert {r["node"] for r in rows} == {"unit:OEM-24-0398"}
    assert {(r["othersys"], r["othervalue"]) for r in rows} >= {("MES", "OEM-24-0398")}
    # a retired R2 tag and its replacement are the same signal
    sigs = kg.sparql("""PREFIX ftf: <https://domain-explorer.dev/ftf#>
        SELECT ?s WHERE { ?s a ftf:Signal ; ftf:measures_position <https://domain-explorer.dev/ftf/id/pos/R2/30-P-301A> ; ftf:quantity "vibration_de" }""")
    assert {s["s"] for s in sigs} == {"sig:30P301A.VIB_DE", "sig:30P301A_VIB_DE"}  # old and new tag, one position


def test_review_queue_and_human_decisions(world_dir, kg_dir):
    q = json.loads((kg_dir / "review_queue.json").read_text())
    assert q and all(x["status"] == "open" for x in q)
    truth = {tuple(r[:3]): r[3] for r in json.loads((world_dir / "truth.json").read_text())}
    dec = {x["id"]: truth[(x["system"], x["table"], x["key"])] for x in q if (x["system"], x["table"], x["key"]) in truth}
    m = build_kg(world_dir, kg_dir.parent / "kg_after", skip_shacl=True, decisions=dec)
    before = json.loads((kg_dir / "metrics.json").read_text())
    assert m["resolution"]["recall"] >= before["resolution"]["recall"] and m["resolution"]["precision"] >= 0.98
    assert m["review_queue"] <= before["review_queue"]


def test_every_inferred_link_has_provenance(kg_dir):
    ttl = (kg_dir / "provenance.ttl").read_text()
    assert "LinkAssertion" in ttl and "tag_rule" in ttl and "alias_table" in ttl
    links = json.loads((kg_dir / "links.json").read_text())
    assert all(l["conf"] >= 0.9 for l in links)
    assert all(l["method"] and l["evidence"] for l in links)
