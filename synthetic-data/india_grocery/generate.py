"""
Synthetic India grocery world: one Bengaluru supermarket, its DC and its dairy route.

Observable tables (what the store's, the DC's and the payment provider's systems record):
  locations, products, pos_bills, pos_lines, inventory_book_daily, forecasts, store_orders,
  shipments, dc_pick_confirmations, asn_lines, pallets, goods_receipts, receiving_claims,
  dc_stock_adjustments, dsd_deliveries, write_offs, stock_counts, shelf_audits,
  pos_payments, psp_upi_report, upi_settlements, upi_refunds, customer_complaints (June)
Truth tables (invisible to the store; the answer key for exercises and demos):
  truth_hourly, truth_pallets, truth_scan_errors, truth_events, truth_payments
Also writes answer_key.json and realism_report.txt next to the tables.

The world runs eight weeks (4 May to 28 June 2026, the last four are the story) with the
store as it operates today. Interventions are explored by export_blog.py.

Run:
    python synthetic-data/india_grocery/generate.py --seed 42
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import common

from india_grocery import answer_key, payments, realism, spec
from india_grocery.world import (
    AS_IS,
    DAYS,
    OPEN_HOURS,
    Draws,
    World,
    build_bills,
    simulate,
)

SUBDOMAIN = spec.SUBDOMAIN


def frames(w: World, bills: list[dict], lines: list[dict], pay: payments.Payments | None = None) -> dict[str, pd.DataFrame]:
    pay = pay or payments.simulate_payments(bills, payments.AS_TODAY, w.seed)
    products = pd.DataFrame([{
        "sku": p.sku, "gtin": p.gtin, "name": p.name, "category": p.category, "family": p.family, "pack": p.pack,
        "price_inr": p.price, "cost_inr": p.cost, "case_units": p.case_units, "flow": p.flow,
        "shelf_capacity": p.shelf_capacity or None, "shelf_life_days": p.shelf_life_days,
    } for p in spec.PRODUCTS])
    pos_lines = pd.DataFrame(lines)
    scan_errors = pos_lines[pos_lines["sku_scanned"] != pos_lines["sku_actual"]][
        ["bill_id", "line", "sku_scanned", "sku_actual", "qty"]].reset_index(drop=True)
    book = pd.DataFrame([{"date": d.isoformat(), "sku": s, "book_on_hand_close": int(w.daily[s]["book_close"][i])}
                         for s in spec.BY_SKU for i, d in enumerate(DAYS)])
    resp = list(spec.param("oos_response"))  # type: ignore[arg-type]
    truth_hourly = []
    for s in spec.BY_SKU:
        hw = w.hourly[s]
        for i, d in enumerate(DAYS):
            for j, hour in enumerate(OPEN_HOURS):
                row = {"date": d.isoformat(), "hour": hour, "sku": s,
                       "demand_base": int(hw["demand_base"][i, j]), "demand": int(hw["demand"][i, j]),
                       "sold": int(hw["sold"][i, j]), "lost": int(hw["lost"][i, j]),
                       "empty_fraction": round(float(hw["empty"][i, j]), 3), "cause": w.causes[s][i][j],
                       "shelf": int(hw["shelf"][i, j]), "backroom": int(hw["back"][i, j]),
                       "misplaced": int(hw["lost_stock"][i, j]), "book": int(hw["book"][i, j]),
                       "substitutes_in": int(hw["subs_in"][i, j])}
                row.update({f"lost_{k}": int(hw[k][i, j]) for k in resp})
                truth_hourly.append(row)
    shipments = pd.DataFrame(w.shipments).drop(columns=["arrival_minute"])
    counts = pd.DataFrame(w.counts).rename(columns={"misplaced_found": "found_in_wrong_bay_units"})
    return {
        "locations": pd.DataFrame(spec.LOCATIONS),
        "products": products,
        "pos_bills": pd.DataFrame(bills).rename(columns={"other_merchandise_inr": "other_items_inr"}),
        "pos_lines": pos_lines.drop(columns=["sku_actual"]),
        "inventory_book_daily": book,
        "forecasts": pd.DataFrame(w.forecasts),
        "store_orders": pd.DataFrame(w.orders),
        "shipments": shipments,
        "dc_pick_confirmations": pd.DataFrame(w.picks),
        "asn_lines": pd.DataFrame(w.asn_lines),
        "pallets": pd.DataFrame(w.pallets),
        "goods_receipts": pd.DataFrame(w.receipts),
        "receiving_claims": pd.DataFrame(w.claims, columns=[
            "claim_id", "claim_ts", "shipment_id", "sscc", "line", "notice_sku", "notice_units", "received_sku",
            "received_units", "found_by"]),
        "dc_stock_adjustments": pd.DataFrame(w.dc_adjustments, columns=[
            "adjusted_ts", "sku", "slot", "cases", "units", "value_at_cost_inr", "reason"]),
        "dsd_deliveries": pd.DataFrame(w.dsd),
        "write_offs": pd.DataFrame(w.write_offs),
        "stock_counts": counts,
        "shelf_audits": pd.DataFrame(w.audits),
        "truth_hourly": pd.DataFrame(truth_hourly),
        "truth_pallets": pd.DataFrame(w.pallets_truth),
        "truth_scan_errors": scan_errors,
        "truth_events": pd.DataFrame(w.events).drop(columns=["scenario"]),
        "pos_payments": pd.DataFrame([{k: a[k] for k in ("bill_id", "attempt", "ts", "tender", "amount_inr",
                                                          "till_status", "rrn", "note")} for a in pay.attempts]),
        "psp_upi_report": pd.DataFrame(pay.psp),
        "upi_settlements": pd.DataFrame(payments.settlements(pay)),
        "upi_refunds": pd.DataFrame(pay.refunds, columns=["refund_id", "rrn", "bill_id", "amount_inr", "trigger",
                                                          "requested_ts", "completed_ts"]),
        "customer_complaints": pd.DataFrame(pay.complaints),
        "truth_payments": pd.DataFrame([{k: a[k] for k in ("bill_id", "attempt", "rrn", "tender", "debited", "final",
                                                            "resolved_ts")} for a in pay.attempts]),
    }


def build_world(seed: int = 42) -> tuple[World, Draws, list[dict], list[dict]]:
    dr = Draws(seed)
    w = simulate(AS_IS, seed, dr, record_bills=True)
    bills, lines = build_bills(w, dr)
    w.bills = bills
    return w, dr, bills, lines


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    w, dr, bills, lines = build_world(seed)
    tables = frames(w, bills, lines)
    for name, df in tables.items():
        common.write_table(SUBDOMAIN, name, df)
    res = realism.checks(w, dr)
    key = answer_key.build(w, res)
    out = common.output_dir_for(SUBDOMAIN)
    (out / "answer_key.json").write_text(json.dumps(key, indent=2, sort_keys=True, default=str) + "\n")
    (out / "realism_report.txt").write_text(realism.report(res) + "\n")
    return tables


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(seed=args.seed)
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")
    print((common.output_dir_for(SUBDOMAIN) / "realism_report.txt").read_text())


if __name__ == "__main__":
    main()
