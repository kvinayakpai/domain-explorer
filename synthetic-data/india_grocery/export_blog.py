"""
Export the slice of the India grocery world that the "Why Domain Matters" blog uses.

Runs the store-side intervention grid, the milk standing-order grid and the DC and
receiving grid on the same customers (common random numbers), computes what each persona
sees, and writes:

  <out>/src/data/retail.json                       data for the retail demo
  <out>/src/data/logistics.json                    data for the logistics demo
  <out>/src/data/payments.json                     data for the payments demo
  <out>/public/data/india-grocery/*.csv            June records readers can download
  <out>/public/data/india-grocery/answer-key-retail.json
  <out>/public/data/india-grocery/answer-key-logistics.json
  <out>/public/data/india-grocery/answer-key-payments.json
  <out>/public/data/india-grocery/README.md

Run:
    python synthetic-data/india_grocery/export_blog.py --out ../domain-series
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from india_grocery import answer_key, payments, realism, spec
from india_grocery.generate import build_world
from india_grocery.world import DAYS, STORY_FIRST, Draws, Scenario, World, simulate

HERO = spec.HERO_SKU
ATTA = [s for s in spec.DC_SKUS if spec.BY_SKU[s].family == "atta"]
SHORT = {"ATTA-WW-5KG": "5kg", "ATTA-WW-1KG": "1kg", "ATTA-WW-10KG": "10kg"}
JUNE = slice(STORY_FIRST, None)
ALERTS = {"off": None, "2d": 2, "1d": 1}
ROUTINES = {"today": False, "scanned": True}
MILK_FACTORS = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]
DC_CHECKS = ["none", "pick_scan", "check_weigh"]
RECEIVING = ["label", "case_scan"]
WRONG_DAY = date(2026, 6, 22)
WINDOW = (date(2026, 6, 20), spec.END)  # the logistics demo's charts
LOGISTICS_KINDS = {"wrong_pallet", "pick_scan_caught_wrong_item", "check_weigh_caught_wrong_item",
                   "receiving_scan_caught_mismatch", "put_away_scan_caught_mismatch", "dc_short_pick",
                   "dc_cycle_count", "complaint_count", "dc_short_ship"}


def _ints(a) -> list[int]:
    return [round(float(x)) for x in a]


def _june(a) -> list:
    return a[JUNE].reshape(-1).tolist()


def scenario_block(w: World, alert: str, routine: str) -> dict:
    h, d = w.hourly[HERO], w.daily[HERO]
    return {
        "key": f"{alert}|{routine}",
        "alert": alert,
        "routine": routine,
        "hourly": {
            "shelf": _ints(_june(h["shelf"])), "backroom": _ints(_june(h["back"])),
            "misplaced": _ints(_june(h["lost_stock"])), "book": _ints(_june(h["book"])),
            "demand": _ints(_june(h["demand"])), "sold": _ints(_june(h["sold"])),
            "empty": [round(float(x), 2) for x in _june(h["empty"])],
        },
        "daily": {
            "recorded": {SHORT[s]: _ints(w.daily[s]["scanned"][JUNE]) for s in ATTA},
            "demand": _ints(d["demand"][JUNE]),
            # The forecast that drove day t was made at 22:00 the night before.
            "forecast": [round(float(x), 1) for x in d["forecast"][STORY_FIRST - 1:-1]],
            "reorder_point": _ints(d["reorder_point"][STORY_FIRST - 1:-1]),
            "ordered": _ints(d["ordered"][JUNE]),
            "received_book": _ints(d["received_book"][JUNE]),
            "received_physical": _ints(d["received_physical"][JUNE]),
            "book_close": _ints(d["book_close"][JUNE]),
            "physical_close": _ints(d["physical_close"][JUNE]),
            "lost": _ints(d["lost"][JUNE]),
        },
        "kpis": answer_key.kpis(w),
        "episodes": answer_key.episodes(w, HERO),
        "events": [e for e in w.events if e["ts"] >= "2026-06" and e["sku"] in ATTA],
        "counts": [c for c in w.counts if c["count_ts"] >= "2026-06" and c["sku"] in ATTA],
    }


def milk_block(w: World, factor: float) -> dict:
    s = "MILK-TONED-500ML"
    d = w.daily[s]
    by_day = {x["date"]: x["units"] for x in w.write_offs if x["sku"] == s and x["reason"] == "expired"}
    return answer_key.milk(w) | {
        "factor": factor,
        "daily_lost": _ints(d["lost"][JUNE]),
        "daily_expired": [by_day.get(day.isoformat(), 0) for day in DAYS[STORY_FIRST:]],
    }


def logistics_block(w: World, dc: str, rv: str) -> dict:
    """What each logistics persona sees for one DC check and one way of receiving."""
    o = answer_key.otif(w)
    d22 = DAYS.index(WRONG_DAY)
    lo, hi = DAYS.index(WINDOW[0]), DAYS.index(WINDOW[1]) + 1
    d5 = w.daily[HERO]
    h5, h1 = w.hourly[HERO], w.hourly["ATTA-WW-1KG"]
    ship = next(s for s in w.shipments if s["arrived_ts"].startswith(WRONG_DAY.isoformat()))
    sid = ship["shipment_id"]
    lost = int(d5["lost"][d22:].sum())

    def win(a) -> list:
        return a[lo:hi].reshape(-1).tolist()

    return {
        "key": f"{dc}|{rv}", "dc_check": dc, "receiving": rv,
        "kpis": {"otif": o["ways"], "good": o["good"], "out_of": o["out_of"], "case_fill": o["case_fill"],
                 "in_slot": o["in_slot"], "shipments": o["shipments"],
                 "empty_open_hours_after": round(float(d5["empty_hours"][d22:].sum()), 1),
                 "lost_units_after": lost, "lost_value_after_inr": round(lost * spec.BY_SKU[HERO].price, 0)},
        "hourly": {"book_5kg": _ints(win(h5["book"])), "shelf_5kg": _ints(win(h5["shelf"])),
                   "empty_5kg": [round(float(x), 2) for x in win(h5["empty"])],
                   "demand_5kg": _ints(win(h5["demand"])),
                   "book_1kg": _ints(win(h1["book"])),
                   "physical_1kg": _ints(win(h1["shelf"] + h1["back"] + h1["lost_stock"]))},
        "by_shipment": o["by_shipment"],
        "shipment": {k: v for k, v in ship.items() if k != "arrival_minute"},
        "picks": [p for p in w.picks if p["shipment_id"] == sid],
        "notice": [a for a in w.asn_lines if a["shipment_id"] == sid],
        "pallets": [p for p in w.pallets if p["shipment_id"] == sid],
        "receipts": [r for r in w.receipts if r["shipment_id"] == sid],
        "claims": [c for c in w.claims if c["claim_ts"] >= "2026-06"],
        "dc_adjustments": w.dc_adjustments,
        "store_counts": [c for c in w.counts if c["count_ts"] >= WRONG_DAY.isoformat() and c["sku"] in ATTA
                         and c["trigger"] != "scheduled full count"],
        "events": sorted([e for e in w.events if e["ts"] >= "2026-06" and e["kind"] in LOGISTICS_KINDS],
                         key=lambda e: e["ts"]),
        "episodes": [e for e in answer_key.episodes(w, HERO) if e["start"] >= WRONG_DAY.isoformat()],
    }


def logistics_records(w: World) -> dict:
    """June's shipping records, as the systems keep them, for the demo's record drawer."""
    june = "2026-06"
    truth = {(t["sscc"], t["line"]): t for t in w.pallets_truth}
    rec = {(r["sscc"], r["line"]): r for r in w.receipts}
    notice = []
    for a in w.asn_lines:
        if a["shipment_id"] < "SHP-2606":
            continue
        t, r = truth[(a["sscc"], a["line"])], rec[(a["sscc"], a["line"])]
        notice.append({k: a[k] for k in ("shipment_id", "sscc", "line", "sku", "cases", "units")}
                      | {"booked_sku": r["sku_booked"], "booked_units": r["units_booked"],
                         "really": None if t["sku_actual"] == a["sku"] else
                         {"sku": t["sku_actual"], "units": t["units_actual"]}})
    return {
        "shipments": [{k: v for k, v in s.items() if k != "arrival_minute"} for s in w.shipments
                      if s["arrived_ts"] >= june],
        "notice": notice,
        "picks": [p for p in w.picks if p["pick_ts"] >= june],
        "pallets": [p for p in w.pallets if p["shipment_id"] >= "SHP-2606"],
    }


TILLS = ["retry", "check"]
RECONS = ["manual", "bill_ref"]
DRAWER = ("2026-06-20T18:00", "2026-06-20T20:30")


def payments_block(pay: payments.Payments, bills: list[dict]) -> dict:
    """What each payments persona sees under one till policy and one way of reconciling."""
    slow = answer_key.SLOWDOWN
    june = answer_key.JUNE_RANGE
    by_bill: dict[str, list[dict]] = {}
    for a in pay.attempts:
        by_bill.setdefault(a["bill_id"], []).append(a)
    day = slow[0][:10]
    hourly = []
    for hour in spec.OPEN_HOURS:
        h = f"{day}T{hour:02d}"
        upi = [a for a in pay.attempts if a["tender"] == "UPI" and a["ts"][:13] == h]
        hourly.append({"hour": hour, "upi_attempts": len(upi),
                       "approved_at_till": sum(a["till_status"].startswith("approved") for a in upi),
                       "credited": sum(a["final"] in ("success", "late credit") for a in upi)})
    days = [d.isoformat() for d in DAYS[STORY_FIRST:]]
    daily = []
    for d in days:
        upi = [a for a in pay.attempts if a["tender"] == "UPI" and a["ts"][:10] == d]
        credits = [a for a in pay.attempts if a["tender"] == "UPI" and a["final"] in ("success", "late credit")
                   and a["resolved_ts"][:10] == d]
        daily.append({"date": d, "till_approved": sum(a["till_status"].startswith("approved") for a in upi),
                      "provider_credits": len(credits),
                      "unmatched": sum(1 for x in pay.doubles if x["credited_ts"][:10] == d),
                      "refunds": sum(1 for f in pay.refunds if f["completed_ts"][:10] == d)})
    return {
        "key": pay.scenario.key, "till": pay.scenario.till, "recon": pay.scenario.recon,
        "kpis": {"june": payments.kpis(pay, bills, *june),
                 "slowdown": {**payments.kpis(pay, bills, *slow), "till_minutes": payments.till_minutes(pay, *slow)},
                 "refunds": payments.refunds_summary(pay)},
        "doubles": [d | {"attempts": [{k: a[k] for k in ("attempt", "ts", "tender", "till_status", "final")}
                                      for a in by_bill[d["bill_id"]]]} for d in pay.doubles],
        "returns": pay.returns,
        "complaints": sorted(pay.complaints, key=lambda c: c["complaint_ts"]),
        "refunds": pay.refunds,
        "hourly": hourly,
        "daily": daily,
    }


def payments_records(pay: payments.Payments) -> dict:
    """The till's and the provider's records around the slowdown, as the systems keep them."""
    lo, hi = DRAWER
    att = [a for a in pay.attempts if lo <= a["ts"][:16] < hi]
    rrns = {a["rrn"] for a in att if a["rrn"]}
    return {
        "pos": [{k: a[k] for k in ("bill_id", "attempt", "ts", "tender", "amount_inr", "till_status")}
                | {"rrn": a["till_rrn"],
                   "really": a["final"] if a["tender"] == "UPI" and a["final"] in ("late credit", "returned") else None}
                for a in att],
        "psp": [r for r in pay.psp if r["rrn"] in rrns],
        "settlements": payments.settlements(pay),
    }


def payments_downloads(out: Path, w: World, pay: payments.Payments) -> None:
    write_csv(out / "pos-payments-june.csv", [a | {"rrn": a["till_rrn"]} for a in pay.attempts],
              ["bill_id", "attempt", "ts", "tender", "amount_inr", "till_status", "rrn", "note"])
    write_csv(out / "psp-upi-report-june.csv", pay.psp,
              ["rrn", "initiated_ts", "amount_inr", "status", "status_ts", "bill_ref"])
    write_csv(out / "upi-settlements-june.csv", payments.settlements(pay),
              ["settlement_date", "upi_credits", "gross_inr", "refunds_inr", "mdr_inr", "net_inr"])
    write_csv(out / "upi-refunds-june.csv", pay.refunds,
              ["refund_id", "rrn", "bill_id", "amount_inr", "trigger", "requested_ts", "completed_ts"])
    write_csv(out / "customer-complaints-june.csv", sorted(pay.complaints, key=lambda c: c["complaint_ts"]),
              ["complaint_ts", "kind", "amount_inr", "bill_id", "rrn", "resolved_ts", "resolution"])
    key = {
        "about": "Answer key for the payments exercises. It holds what happened to each customer's money.",
        "story": answer_key.payments_story(w, pay),
        "charged_twice": pay.doubles,
        "debited_and_returned": pay.returns,
        "upi_attempts_not_simply_approved": [
            {k: a[k] for k in ("bill_id", "attempt", "ts", "rrn", "amount_inr", "till_status", "debited", "final",
                               "resolved_ts")}
            for a in pay.attempts if a["tender"] == "UPI" and a["till_status"] != "approved"],
    }
    (out / "answer-key-payments.json").write_text(json.dumps(key, indent=2, default=str) + "\n")


def records(w: World, bills: list[dict], lines: list[dict]) -> dict:
    """Small excerpts for the demo's record drawer (incident week)."""
    ts = {b["bill_id"]: b["bill_ts"] for b in bills}
    week = ("2026-06-09", "2026-06-14")
    atta_lines = [ln | {"bill_ts": ts[ln["bill_id"]]} for ln in lines
                  if ln["sku_scanned"] in ATTA or ln["sku_actual"] in ATTA]
    return {
        "pos_lines": [{k: ln[k] for k in ("bill_id", "bill_ts", "sku_scanned", "qty", "unit_price", "line_amount")}
                      | {"scan_error": ln["sku_actual"] if ln["sku_actual"] != ln["sku_scanned"] else None}
                      for ln in atta_lines if week[0] <= ln["bill_ts"][:10] <= week[1]],
        "forecasts": [f for f in w.forecasts if f["sku"] == HERO and f["date"] >= "2026-06"],
        "receipts": [r for r in w.receipts if r["sku_booked"] in ATTA and r["received_ts"] >= "2026-06"],
        "audits": [a for a in w.audits if a["sku"] == HERO],
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(rows)


def downloads(out: Path, w: World, bills: list[dict], lines: list[dict]) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    june = "2026-06"
    bill = {b["bill_id"]: b for b in bills}
    pos = [ln | {"bill_ts": bill[ln["bill_id"]]["bill_ts"]} for ln in lines if ln["sku_scanned"] in ATTA]
    pos = [p for p in pos if p["bill_ts"] >= june]
    write_csv(out / "pos-lines-atta-june.csv", pos,
              ["bill_id", "bill_ts", "line", "gtin_scanned", "sku_scanned", "qty", "unit_price", "line_amount"])
    daily = [{"date": d.isoformat(), "sku": s, "units_sold": int(w.daily[s]["scanned"][i]),
              "revenue_inr": round(float(w.daily[s]["revenue"][i]), 2)}
             for s in spec.BY_SKU for i, d in enumerate(DAYS) if i >= STORY_FIRST]
    write_csv(out / "daily-sales-june.csv", daily, ["date", "sku", "units_sold", "revenue_inr"])
    book = [{"date": d.isoformat(), "sku": s, "book_on_hand_close": int(w.daily[s]["book_close"][i])}
            for s in spec.BY_SKU for i, d in enumerate(DAYS) if i >= STORY_FIRST]
    write_csv(out / "inventory-book-june.csv", book, ["date", "sku", "book_on_hand_close"])
    write_csv(out / "forecasts-june.csv", [f for f in w.forecasts if f["date"] >= june],
              ["date", "sku", "forecast_units_per_day", "sigma", "reorder_point", "order_up_to", "book_on_hand",
               "on_order", "ordered_units", "method"])
    write_csv(out / "store-orders-june.csv", [o for o in w.orders if o["created_ts"] >= june],
              ["order_id", "sku", "units", "cases", "created_ts", "reason"])
    asn = {(a["sscc"], a["line"]): a for a in w.asn_lines}
    receipts = [r | {"asn_sku": asn[(r["sscc"], r["line"])]["sku"], "asn_units": asn[(r["sscc"], r["line"])]["units"]}
                for r in w.receipts if r["received_ts"] >= june]
    write_csv(out / "goods-receipts-june.csv", receipts,
              ["grn_id", "shipment_id", "sscc", "line", "received_ts", "asn_sku", "asn_units", "sku_booked",
               "units_booked", "receipt_method"])
    write_csv(out / "stock-counts-june.csv", [c for c in w.counts if c["count_ts"] >= june],
              ["count_ts", "sku", "book_before", "counted", "adjustment", "trigger"])
    write_csv(out / "shelf-audits-june.csv", w.audits, ["audit_ts", "sku", "status"])
    write_csv(out / "write-offs-june.csv", [x for x in w.write_offs if x["date"] >= june],
              ["date", "sku", "units", "reason"])
    errors = [{"bill_id": ln["bill_id"], "bill_ts": bill[ln["bill_id"]]["bill_ts"], "sku_scanned": ln["sku_scanned"],
               "sku_actual": ln["sku_actual"], "qty": ln["qty"]}
              for ln in lines if ln["sku_actual"] != ln["sku_scanned"] and ln["sku_actual"] in ATTA]
    truth = {
        "about": "Answer key for the retail exercises. It holds what the store could not see.",
        "story": answer_key.retail_story(w),
        "episodes_5kg": answer_key.episodes(w, HERO),
        "scan_errors_atta_june": [e for e in errors if e["bill_ts"] >= june],
        "close_of_day_truth_5kg": [
            {"date": d.isoformat(), "book": int(w.daily[HERO]["book_close"][i]),
             "physical": int(w.daily[HERO]["physical_close"][i]), "true_demand": int(w.daily[HERO]["demand"][i]),
             "units_sold": int(w.daily[HERO]["sold"][i]), "lost": int(w.daily[HERO]["lost"][i])}
            for i, d in enumerate(DAYS) if i >= STORY_FIRST],
    }
    (out / "answer-key-retail.json").write_text(json.dumps(truth, indent=2, default=str) + "\n")
    logistics_downloads(out, w)
    return sorted(p.name for p in out.iterdir())


def logistics_downloads(out: Path, w: World) -> None:
    june = "2026-06"
    write_csv(out / "products.csv", [
        {"sku": p.sku, "gtin": p.gtin, "name": p.name, "pack": p.pack, "case_units": p.case_units,
         "case_kg": spec.CASE_KG.get(p.sku), "flow": p.flow, "dc_slot": spec.DC_SLOTS.get(p.sku),
         "price_inr": p.price, "cost_inr": p.cost} for p in spec.PRODUCTS],
        ["sku", "gtin", "name", "pack", "case_units", "case_kg", "flow", "dc_slot", "price_inr", "cost_inr"])
    write_csv(out / "shipments-june.csv", [s for s in w.shipments if s["arrived_ts"] >= june],
              ["shipment_id", "vehicle", "dispatched_ts", "slot_start", "slot_end", "arrived_ts", "pallets"])
    write_csv(out / "dc-pick-confirmations-june.csv", [p for p in w.picks if p["pick_ts"] >= june],
              ["pick_ts", "order_id", "shipment_id", "line", "sku", "slot", "cases_ordered", "cases_confirmed",
               "confirmed_by"])
    write_csv(out / "shipping-notice-lines-june.csv", [a for a in w.asn_lines if a["shipment_id"] >= "SHP-2606"],
              ["shipment_id", "sscc", "line", "order_id", "sku", "gtin", "cases", "units"])
    write_csv(out / "pallets-june.csv", [p for p in w.pallets if p["shipment_id"] >= "SHP-2606"],
              ["sscc", "shipment_id", "cases", "notice_kg", "weight_check"])
    write_csv(out / "dc-stock-adjustments-june.csv", w.dc_adjustments,
              ["adjusted_ts", "sku", "slot", "cases", "units", "value_at_cost_inr", "reason"])
    o = answer_key.otif(w)
    key = {
        "about": "Answer key for the logistics exercises. It holds what was really on the pallets.",
        "story": answer_key.logistics_story(w),
        "otif_four_ways": {k: v for k, v in o.items() if k != "by_shipment"},
        "otif_by_delivery": o["by_shipment"],
        "pallet_contents_june": [t for t in w.pallets_truth if t["shipment_id"] >= "SHP-2606"],
    }
    (out / "answer-key-logistics.json").write_text(json.dumps(key, indent=2, default=str) + "\n")


README = """# India grocery world: June records

Synthetic, seeded (seed {seed}) records from one fictional supermarket in Bengaluru (Store 014),
its warehouse and its milk route, generated by the Domain Explorer project
(`synthetic-data/india_grocery`, commit {commit}). Identifiers use GS1 prefix 29, which GS1
sets aside for restricted circulation within a company or a region, so none of them is a
globally issued product number.

These are the records the store's, the warehouse's and the payment provider's systems keep.
They do not show what was really on the shelf, on the pallets, or in customers' accounts.

| File | What it holds |
|---|---|
| products.csv | Items, barcodes, case sizes and weights, and each item's slot in the warehouse |
| pos-lines-atta-june.csv | Every till line for the three atta packs, as scanned |
| daily-sales-june.csv | Units and revenue per item per day, as scanned |
| inventory-book-june.csv | The system's stock on hand at close, per item per day |
| forecasts-june.csv | The nightly forecast, reorder point and order for each warehouse item |
| store-orders-june.csv | Orders sent to the warehouse |
| dc-pick-confirmations-june.csv | The warehouse's pick confirmations for the store's orders |
| shipping-notice-lines-june.csv | What each shipping notice said was on each pallet |
| pallets-june.csv | One row per pallet label (SSCC): cases and the weight its notice implies |
| shipments-june.csv | Trucks: dispatch, delivery slot and arrival |
| goods-receipts-june.csv | Pallets received, with what the shipping notice said and what was booked |
| dc-stock-adjustments-june.csv | Corrections the warehouse made to its stock of the store's lines |
| stock-counts-june.csv | Physical counts at the store and the adjustments they made |
| shelf-audits-june.csv | Twice-weekly shelf audits at 11:00 |
| write-offs-june.csv | Damaged and expired stock written off |
| pos-payments-june.csv | Every payment attempt at the tills, with the till's status and the UPI reference (RRN) |
| psp-upi-report-june.csv | The payment provider's report: each UPI payment's final status and when it was known |
| upi-settlements-june.csv | The acquirer's daily UPI settlement, credits and refunds |
| upi-refunds-june.csv | Refunds the store made for UPI payments |
| customer-complaints-june.csv | Customer complaints about payments |
| answer-key-retail.json | Spoilers for the retail exercises: what was really on the shelf, and why |
| answer-key-logistics.json | Spoilers for the logistics exercises: what was really on the pallets |
| answer-key-payments.json | Spoilers for the payments exercises: what happened to each customer's money |

Retail: try these before opening the retail answer key.

1. Using only the till lines, find the hours when the 5 kg shelf was probably empty.
2. Compare the book stock with sales. When did the book stop moving, and why did nothing get reordered?
3. Work out on-shelf availability from the shelf audits and compare it with the share of days the system showed stock.
4. Estimate how many bags of 5 kg atta customers wanted but could not buy in the week of 8 June.

Logistics: try these before opening the logistics answer key.

1. Compute June's on-time-in-full from the shipments, shipping notices, receipts and orders: per delivery, then per order line. Why do the two differ?
2. Every record says the 22 June delivery was perfect. Find the evidence, in other tables, that it was not.
3. Line up the warehouse's stock adjustments with the store's count adjustments. What do the four have in common?
4. Using the case weights in products.csv, work out how much lighter the 22 June pallet was than its notice. Would a scale with a 2% tolerance have caught it?

Payments: try these before opening the payments answer key.

1. Using the till's payments alone, find the hour on 20 June when UPI started failing, and how long it lasted.
2. Match the provider's UPI successes to the till's approved payments by reference number. Which credits have no approved payment behind them?
3. For each of those credits, find the bill it belongs to and how the customer paid instead. How many customers were charged twice, and for how much?
4. How long did each of them wait for a refund? Which ones had not been refunded when June closed?
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Export the blog slice of the India grocery world.")
    ap.add_argument("--out", type=Path, required=True, help="path to the domain-series repo")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    w, dr, bills, lines = build_world(args.seed)
    res = realism.checks(w, dr)
    failed = [r for r in res if not r[1]]
    if failed:
        sys.exit("realism checks failed:\n" + realism.report(res))
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                cwd=Path(__file__).parent, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"

    blocks = []
    grid_draws: Draws = dr
    for alert, days in ALERTS.items():
        for routine, disc in ROUTINES.items():
            ws = w if (days is None and not disc) else simulate(Scenario(days, disc), args.seed, grid_draws)
            blocks.append(scenario_block(ws, alert, routine))
    milk = [milk_block(w if f == 1.0 else simulate(Scenario(milk_order_factor=f), args.seed, grid_draws), f)
            for f in MILK_FACTORS]
    p = spec.BY_SKU[HERO]
    data = {
        "meta": {"seed": args.seed, "commit": commit, "source": "domain-explorer/synthetic-data/india_grocery",
                 "store": spec.STORE, "days": [d.isoformat() for d in DAYS[STORY_FIRST:]],
                 "hours": spec.OPEN_HOURS, "realism": [{"check": n, "pass": ok, "detail": det, "source": src}
                                                       for n, ok, det, src in res]},
        "hero": {"sku": p.sku, "name": p.name, "price": p.price, "case_units": p.case_units,
                 "shelf_capacity": p.shelf_capacity, "gtin": p.gtin},
        "scenarios": blocks,
        "milk": milk,
        "milk_product": {"name": spec.BY_SKU["MILK-TONED-500ML"].name,
                         "standing_order": spec.param("milk_standing_order"),
                         "shelf_life": spec.PARAMS["milk_shelf_life_hours"][1]},
        "story": answer_key.retail_story(w),
        "causes": answer_key.causes(w),
        "record_accuracy": {"items": 11, "wrong": sum(c["adjustment"] != 0 for c in w.counts
                                                       if c["count_ts"].startswith(spec.END.isoformat()))},
        "records": records(w, bills, lines),
        "params": {k: {"value": v[0], "source": v[1]} for k, v in spec.PARAMS.items()},
    }
    data_dir = args.out / "src" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "retail.json").write_text(json.dumps(data, separators=(",", ":"), default=str))

    lblocks = []
    for dc in DC_CHECKS:
        for rv in RECEIVING:
            ws = w if (dc == "none" and rv == "label") else simulate(Scenario(dc_check=dc, receiving=rv),
                                                                       args.seed, grid_draws)
            lblocks.append(logistics_block(ws, dc, rv))
    lo, hi = DAYS.index(WINDOW[0]), DAYS.index(WINDOW[1]) + 1
    logistics = {
        "meta": {"seed": args.seed, "commit": commit, "source": data["meta"]["source"], "store": spec.STORE,
                 "dc": spec.DC, "days": [d.isoformat() for d in DAYS[lo:hi]], "hours": spec.OPEN_HOURS,
                 "realism": data["meta"]["realism"]},
        "hero": data["hero"],
        "one_kg": {"sku": "ATTA-WW-1KG", "name": spec.BY_SKU["ATTA-WW-1KG"].name,
                   "case_units": spec.BY_SKU["ATTA-WW-1KG"].case_units, "price": spec.BY_SKU["ATTA-WW-1KG"].price},
        "slots": spec.DC_SLOTS, "case_kg": spec.CASE_KG, "pallet_tare_kg": spec.PALLET_TARE_KG,
        "costs": {p.sku: p.cost for p in spec.PRODUCTS if p.flow == "DC"},
        "check_weigh": {"tolerance": spec.param("check_weigh_tolerance"),
                        "repick_minutes": spec.param("check_weigh_repick_minutes")},
        "definitions": answer_key.OTIF_WAYS,
        "scenarios": lblocks,
        "story": answer_key.logistics_story(w),
        "records": logistics_records(w),
    }
    (data_dir / "logistics.json").write_text(json.dumps(logistics, separators=(",", ":"), default=str))

    u = payments.draws(args.seed, len(payments.june_bills(bills)))
    pays = {f"{t}|{r}": payments.simulate_payments(bills, payments.PayScenario(t, r), args.seed, u)
            for t in TILLS for r in RECONS}
    as_today = pays["retry|manual"]
    pdata = {
        "meta": {"seed": args.seed, "commit": commit, "source": data["meta"]["source"], "store": spec.STORE,
                 "days": [d.isoformat() for d in DAYS[STORY_FIRST:]], "hours": spec.OPEN_HOURS,
                 "slowdown": {"start": answer_key.SLOWDOWN[0], "end": answer_key.SLOWDOWN[1]},
                 "realism": data["meta"]["realism"]},
        "params": {k: {"value": spec.PARAMS[k][0], "source": spec.PARAMS[k][1]}
                   for k in spec.PARAMS if k.startswith(("upi_", "after_upi", "complaint_", "manual_refund", "card_"))},
        "scenarios": [payments_block(pays[k], bills) for k in pays],
        "story": answer_key.payments_story(w, as_today),
        "records": payments_records(as_today),
    }
    (data_dir / "payments.json").write_text(json.dumps(pdata, separators=(",", ":"), default=str))

    dl = args.out / "public" / "data" / "india-grocery"
    files = downloads(dl, w, bills, lines)
    payments_downloads(dl, w, as_today)
    files = sorted(p.name for p in dl.iterdir())
    (dl / "README.md").write_text(README.format(seed=args.seed, commit=commit))
    sizes = ", ".join(f"{n} {(data_dir / n).stat().st_size / 1024:.0f} KB"
                      for n in ("retail.json", "logistics.json", "payments.json"))
    print(f"wrote src/data ({sizes}) and {len(files) + 1} download files")


if __name__ == "__main__":
    main()
