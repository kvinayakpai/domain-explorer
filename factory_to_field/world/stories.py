"""Answer keys for the planted stories, computed from the generated world (never typed in).

The scorer compares agent output with these. Facts a human reviewer can check against the demo
are asserted in tests/test_world.py.
"""
from __future__ import annotations

from ..analytics import km_median
from .model import World, days
from .spec import A07_NEW, A07_OLD, ECO_BEARING, ECO_ELASTOMER, FLEET, LOT_BEARING, LOT_ELASTOMER, TODAY


def build(w: World) -> dict:
    u = w.units
    fleet = sorted(FLEET)
    runs_old = [(r["days"], r["state"] == "failed") for r in w.runs if not r["new_seal"]]
    runs_new = [(r["days"], r["state"] == "failed") for r in w.runs if r["new_seal"]]
    new_strings = [r for r in w.runs if r["new_seal"]]
    lot_pumps = [s for s in w.answer["lot_pumps"]]
    lot_secs = w.answer["lot_sections"]
    customers = lambda serials: sorted({w.customers[u[f"unit:{s}"]["customer"]]["name"] for s in serials})
    expedited = sorted(e["id"] for e in w.ecos.values() if e["route"] == "expedited" and e["waived"])
    a07_runs = sorted((r for r in w.runs if r["well"] == "A-07"), key=lambda r: r["start"])
    key = {
        "today": TODAY.isoformat(),
        "CASE-1042": {
            "position": "R1:10-P-101A",
            "trigger_tag": "10P101A.VIB_DE",
            "as_of": "2026-10-16T07:30:00Z",
            "current_unit": "OEM-25-1187",
            "current_unit_since": "2026-03-10",
            "spare_position": "R1:10-P-101B",
            "spare_unit": "OEM-24-0412",
            "failures": [
                {"unit": "OEM-24-0412", "mode": "VIB", "on": "2026-03-08", "position": "R1:10-P-101A"},
                {"unit": "OEM-24-0412", "mode": "ELP", "on": "2026-09-21", "position": "R1:10-P-101B"},
            ],
            "fleet": fleet,
            "fleet_failed": ["OEM-24-0412", "OEM-24-0455"],
            "fleet_alarm": ["OEM-25-1187"],
            "fleet_peaks": ["OEM-24-0398", "OEM-25-1150"],
            "fleet_normal": ["OEM-25-1203"],
            "bearing_lot": LOT_BEARING,
            "eco": ECO_BEARING,
            "diagnosis": "bearing outer race defect",
            "cavitation_excluded": True,
            "open_work_on_position": 0,
            "bearing_stock": 1,
            "next_window": "2026-10-22",
            "recommendation": "switch to P-101B and repair P-101A in the window",
            "drafts": ["sap_pm.notification", "sap_pm.stock_transfer", "qms.warranty_claim"],
        },
        "CASE-2077": {
            "position": "FA:A-07-ESP",
            "trigger_tag": "A07_MTR_T",
            "as_of": "2026-10-17T04:45:00Z",
            "current_string": A07_NEW,
            "current_string_since": "2026-01-14",
            "current_string_days": days(a07_runs[-1]["start"], TODAY),
            "seal": "SS-25-0811",
            "elastomer_lot": LOT_ELASTOMER,
            "eco": ECO_ELASTOMER,
            "previous_string": A07_OLD,
            "previous_run_days": 688,
            "km_median_old": km_median(runs_old),
            "km_median_new": km_median(runs_new),
            "strings_new": len(new_strings),
            "strings_new_failed": sum(r["state"] == "failed" for r in new_strings),
            "strings_new_running": sum(r["state"] == "running" for r in new_strings),
            "difa_findings": 5,
            "gas_interference_excluded": True,
            "rig_free_from": "2026-10-24",
            "oil_bbl_d": 640,
            "design_limit_c": 150.0,
            "recommendation": "lower the drive frequency and book Rig 2 for 24 Oct",
            "drafts": ["sap_pm.notification", "rigs.request", "qms.warranty_claim"],
        },
        "OEM": {
            "bearing_lot": LOT_BEARING,
            "elastomer_lot": LOT_ELASTOMER,
            "lot_pumps": len(lot_pumps),
            "lot_pump_customers": len(customers(lot_pumps)),
            "lot_sections": len(lot_secs),
            "lot_section_operators": len(customers(lot_secs)),
            "ecos": [ECO_BEARING, ECO_ELASTOMER],
            "waived_expedited": expedited,
            "also_waived": [e for e in expedited if e not in (ECO_BEARING, ECO_ELASTOMER)],
            "root_cause": "expedited alternate-source ECO route with the qualification test waived",
            "press_fit_deficit_pct": 12,
            "drafts": ["qms.eightd", "qms.customer_notice"],
        },
        "TRAPS": {
            "position_vs_unit": {"question": "failures at P-101B in March 2026", "wrong_unit": "OEM-24-0412 (it was at P-101A then)",
                                  "answer": "none at P-101B in March; the 8 March failure happened at P-101A"},
            "as_of": {"position": "R1:10-P-101A", "date": "2026-03-01", "unit": "OEM-24-0412"},
            "stuck_sensor": w.answer["flatline"]["signal"],
            "other_wells_not_lot": [r["well"] for r in w.runs if not r["new_seal"] and r["state"] == "running"],
        },
    }
    return key
