"""Tests for the India grocery world (synthetic-data/india_grocery).

The story numbers pinned here are the ones the "Why Domain Matters" retail post cites.
If the world changes, these fail first, and the post must be updated with them.
"""
from __future__ import annotations

import json
from datetime import date

import numpy as np
import pytest
from india_grocery import answer_key, ids, realism, spec
from india_grocery.world import AS_IS, DAYS, STORY_FIRST, Draws, Scenario, simulate


@pytest.fixture(scope="module")
def draws() -> Draws:
    return Draws(42)


@pytest.fixture(scope="module")
def as_is(draws: Draws):
    return simulate(AS_IS, 42, draws)


def test_gs1_check_digits() -> None:
    # Known-good examples from the GS1 check digit calculator.
    assert ids.check_digit("629104150021") == "3"
    assert ids.is_valid("6291041500213")
    assert ids.is_valid(ids.gtin13(101)) and ids.gtin13(101).startswith("29")
    assert ids.is_valid(ids.sscc18(1001)) and len(ids.sscc18(1001)) == 18


def test_realism_checks_pass(as_is, draws: Draws) -> None:
    res = realism.checks(as_is, draws)
    failed = [r for r in res if not r[1]]
    assert not failed, "\n" + realism.report(res)


def test_deterministic(draws: Draws) -> None:
    a = answer_key.build(simulate(AS_IS, 42, draws), [])
    b = answer_key.build(simulate(AS_IS, 42, Draws(42)), [])
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def test_scenarios_share_customers_and_history(as_is, draws: Draws) -> None:
    for scn in (Scenario(alert_days=1), Scenario(backroom_discipline=True), Scenario(milk_order_factor=0.85),
                Scenario(dc_check="pick_scan"), Scenario(dc_check="check_weigh", receiving="case_scan")):
        w = simulate(scn, 42, draws)
        for s in spec.BY_SKU:
            assert np.array_equal(w.hourly[s]["demand_base"], as_is.hourly[s]["demand_base"])
            assert np.array_equal(w.daily[s]["scanned"][:STORY_FIRST], as_is.daily[s]["scanned"][:STORY_FIRST])


def test_retail_story_numbers_match_the_post(as_is) -> None:
    r = answer_key.retail_story(as_is)
    assert r["misplaced"] == {"ts": "2026-06-09T06:17", "units": 56, "cases": 14}
    ep = r["episode"]
    assert (ep["start"], ep["end"]) == ("2026-06-10T15:48", "2026-06-13T10:00")
    assert ep["empty_open_hours"] == 39.2 and ep["lost_units"] == 71
    assert (ep["book_on_hand_min"], ep["book_on_hand_max"]) == (55, 56)
    assert ep["reorder_point"] == [39, 40]
    assert r["forecast"] == {"before": 24.3, "end_recorded_sales": 20.2, "end_corrected": 25.7}
    osa = r["kpis"]["osa"]
    assert (osa["system_in_stock"], osa["shelf_audit"], osa["open_hours_on_shelf"], osa["demand_served"]) == (
        0.969, 0.75, 0.768, 0.781)


def test_logistics_story_numbers(as_is) -> None:
    lg = answer_key.logistics_story(as_is)
    assert lg["shipment"]["arrived_ts"] == "2026-06-22T06:12"
    assert lg["line"]["units"] == 64 and lg["actual"] == {
        "line": 1, "shipment_id": "SHP-260622", "sku_actual": "ATTA-WW-1KG",
        "sscc": lg["line"]["sscc"], "units_actual": 160}
    assert ids.is_valid(lg["line"]["sscc"])
    # The four stock corrections: two at the DC, days apart; two at the store, after complaints.
    assert [(a["adjusted_ts"], a["sku"], a["cases"]) for a in lg["dc_adjustments"]] == [
        ("2026-06-23T14:20", "ATTA-WW-1KG", -16), ("2026-06-25T10:00", "ATTA-WW-5KG", 16)]
    assert [(c["sku"], c["adjustment"]) for c in lg["corrections"]] == [("ATTA-WW-5KG", -63), ("ATTA-WW-1KG", 157)]
    assert lg["adjustments_net"]["value_at_cost_inr"] == 80
    ep = lg["episode"]
    assert (ep["start"], ep["end"], ep["empty_open_hours"], ep["lost_units"]) == (
        "2026-06-23T15:30", "2026-06-26T22:00", 51.5, 72)


def test_otif_four_ways(draws: Draws) -> None:
    def run(**kw):
        w = simulate(Scenario(**kw), 42, draws)
        return answer_key.otif(w)["ways"], w.daily[spec.HERO_SKU]["lost"][DAYS.index(date(2026, 6, 22)):].sum()

    ways, lost = run()
    assert ways == {"dc_report": 0.92, "by_line": 0.9, "scorecard": 0.88, "at_the_shelf": 0.84} and lost == 72
    # Scanning cases at receipt makes the scorecard worse and the shelf better.
    ways, lost = run(receiving="case_scan")
    assert ways["scorecard"] == ways["at_the_shelf"] == 0.84 and lost == 0
    # Scanning cases at pick prevents the wrong pallet; the scorecard and the shelf agree.
    ways, lost = run(dc_check="pick_scan")
    assert ways["scorecard"] == ways["at_the_shelf"] == 0.88 and lost <= 1
    # Weighing pallets catches it at dispatch, at the cost of a late truck.
    ways, lost = run(dc_check="check_weigh")
    assert ways["dc_report"] == 0.88 and ways["scorecard"] == 0.84 and lost <= 1


def test_interventions_rank_as_expected(draws: Draws) -> None:
    lost = {}
    for scn in (AS_IS, Scenario(alert_days=2), Scenario(alert_days=1), Scenario(backroom_discipline=True)):
        w = simulate(scn, 42, draws)
        lost[scn.key] = w.daily[spec.HERO_SKU]["lost"][STORY_FIRST:].sum()
    as_is, two, one, routine = lost.values()
    assert as_is > two > one > routine


def test_milk_order_trades_waste_for_gaps(draws: Draws) -> None:
    lean = answer_key.milk(simulate(Scenario(milk_order_factor=0.85), 42, draws))
    rich = answer_key.milk(simulate(Scenario(milk_order_factor=1.15), 42, draws))
    assert lean["unmet_share"] > rich["unmet_share"]
    assert lean["waste_share"] < rich["waste_share"]


def test_calendar() -> None:
    assert DAYS[0] == spec.HISTORY_START and DAYS[-1] == spec.END
    assert DAYS[STORY_FIRST] == spec.STORY_START and spec.STORY_START.weekday() == 0
