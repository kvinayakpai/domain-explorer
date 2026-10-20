"""
Export the slice of the India grocery world that the "Why Domain Matters" blog uses.

Runs the store-side intervention grid and the milk standing-order grid on the same
customers (common random numbers), computes what each persona sees, and writes:

  <out>/src/data/retail.json                       data for the retail demo
  <out>/public/data/india-grocery/*.csv            June records readers can download
  <out>/public/data/india-grocery/answer-key-retail.json
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from india_grocery import answer_key, realism, spec
from india_grocery.generate import build_world
from india_grocery.world import DAYS, STORY_FIRST, Draws, Scenario, World, simulate

HERO = spec.HERO_SKU
ATTA = [s for s in spec.DC_SKUS if spec.BY_SKU[s].family == "atta"]
SHORT = {"ATTA-WW-5KG": "5kg", "ATTA-WW-1KG": "1kg", "ATTA-WW-10KG": "10kg"}
JUNE = slice(STORY_FIRST, None)
ALERTS = {"off": None, "2d": 2, "1d": 1}
ROUTINES = {"today": False, "scanned": True}
MILK_FACTORS = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]


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
    return sorted(p.name for p in out.iterdir())


README = """# India grocery world: June records

Synthetic, seeded (seed {seed}) records from one fictional supermarket in Bengaluru (Store 014),
its warehouse and its milk route, generated by the Domain Explorer project
(`synthetic-data/india_grocery`, commit {commit}). Identifiers use GS1 prefix 29, which GS1
sets aside for restricted circulation within a company or a region, so none of them is a
globally issued product number.

These are the records the store's systems keep. They do not show what was really on the shelf.

| File | What it holds |
|---|---|
| pos-lines-atta-june.csv | Every till line for the three atta packs, as scanned |
| daily-sales-june.csv | Units and revenue per item per day, as scanned |
| inventory-book-june.csv | The system's stock on hand at close, per item per day |
| forecasts-june.csv | The nightly forecast, reorder point and order for each warehouse item |
| store-orders-june.csv | Orders sent to the warehouse |
| goods-receipts-june.csv | Pallets received, with what the shipping notice said and what was booked |
| stock-counts-june.csv | Physical counts and the adjustments they made |
| shelf-audits-june.csv | Twice-weekly shelf audits at 11:00 |
| write-offs-june.csv | Damaged and expired stock written off |
| answer-key-retail.json | Spoilers: what was really on the shelf, and why |

Try these before opening the answer key:

1. Using only the till lines, find the hours when the 5 kg shelf was probably empty.
2. Compare the book stock with sales. When did the book stop moving, and why did nothing get reordered?
3. Work out on-shelf availability from the shelf audits and compare it with the share of days the system showed stock.
4. Estimate how many bags of 5 kg atta customers wanted but could not buy in the week of 8 June.
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
    dl = args.out / "public" / "data" / "india-grocery"
    files = downloads(dl, w, bills, lines)
    (dl / "README.md").write_text(README.format(seed=args.seed, commit=commit))
    size = (data_dir / "retail.json").stat().st_size
    print(f"wrote src/data/retail.json ({size / 1024:.0f} KB) and {len(files) + 1} download files")


if __name__ == "__main__":
    main()
