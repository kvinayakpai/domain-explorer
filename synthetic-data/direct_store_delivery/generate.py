"""
Synthetic Direct Store Delivery (DSD) data — SAP DSD / Aldata Apollo Route
Accounting / Trimble Roadnet + PeopleNet ELD / Epicor DSD + Eagle / Salient
CMx / AFS DSD / ToolsGroup / Descartes / WorkWave / Manhattan Active Routing
+ Honeywell/Zebra rugged handhelds + retailer EDI 894/895/940/945.

Entities (>=10):
  route, driver, vehicle, stop, dsd_order, dsd_order_line, settlement,
  epod_event, perfect_store_audit, route_telemetry, deduction, outlet, account.

Realism:
  - 500 routes × ~50 stops × 90 service days × ~10 line items per stop
    => order_lines ~ 22.5M rows (stops × lines, downsampled from the full 250d).
  - 500 drivers, 500 vehicles, ~25k stops/day → ~2.25M stops over 90 days.
  - 100k perfect-store audits stratified across outlets.
  - ~5M telemetry rows (per-vehicle daily summary; not the raw sub-second feed).
  - ~50k retailer deductions, with EPOD-evidence linkage probability ~0.85.
  - All large-range integer IDs use the int64-safe pattern from
    capital_markets/generate.py (rng.integers + zero-padded format string).

Run:
    python synthetic-data/direct_store_delivery/generate.py
    python synthetic-data/direct_store_delivery/generate.py --service-days 30
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "direct_store_delivery"

# ---------------------------------------------------------------------------
# Reference distributions

ROUTE_TYPES = ["deliver", "presell", "merchandiser", "combination", "service"]
ROUTE_TYPE_W = [0.55, 0.20, 0.10, 0.10, 0.05]

VEHICLE_CLASSES = ["bobtail", "side-bay", "tractor-trailer", "step-van", "sprinter"]
VEHICLE_CLASS_W = [0.32, 0.28, 0.18, 0.16, 0.06]

VEHICLE_MAKES = [
    ("Freightliner", "M2 106"), ("Freightliner", "Cascadia"),
    ("Kenworth", "T370"), ("Kenworth", "T680"),
    ("International", "MV"), ("International", "DuraStar"),
    ("Isuzu", "NPR-HD"), ("Isuzu", "FTR"),
    ("Mercedes-Benz", "Sprinter 3500"),
    ("Ford", "E-450"), ("Ford", "F-650"),
    ("Hino", "338"), ("Volvo", "VHD"),
]

TELEMATICS = ["trimble_peoplenet", "samsara", "geotab", "verizon_connect"]
TELEMATICS_W = [0.42, 0.30, 0.18, 0.10]

PAY_CLASSES = ["hourly", "commission", "hybrid"]
PAY_CLASS_W = [0.55, 0.20, 0.25]

CDL_CLASSES = ["A", "B", "C"]
CDL_CLASS_W = [0.45, 0.50, 0.05]

US_STATES = [
    "CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
    "CO", "MN", "SC", "AL", "LA", "KY", "OR", "OK", "CT", "UT",
]

CHANNELS = ["grocery", "convenience", "drug", "mass", "club", "dollar", "food_service", "ecom"]
CHANNEL_W = [0.34, 0.28, 0.10, 0.08, 0.05, 0.07, 0.07, 0.01]

OUTLET_FORMATS = ["c-store", "grocery", "supercenter", "drug", "club", "express", "food_service"]
OUTLET_FORMAT_W = [0.34, 0.34, 0.08, 0.08, 0.04, 0.06, 0.06]

ORDER_TYPES = ["deliver", "presell", "return", "swap", "service"]
ORDER_TYPE_W = [0.62, 0.28, 0.05, 0.04, 0.01]

ORDER_STATUS = ["draft", "approved", "in_transit", "delivered", "invoiced", "cancelled"]
ORDER_STATUS_W = [0.02, 0.06, 0.05, 0.10, 0.75, 0.02]

PAYMENT_TERMS = ["cod", "net7", "net14", "net30", "charge_account"]
PAYMENT_TERMS_W = [0.32, 0.10, 0.18, 0.30, 0.10]

STOP_STATUS = ["scheduled", "in_route", "on_site", "completed", "skipped", "reattempt"]
STOP_STATUS_W = [0.02, 0.02, 0.02, 0.88, 0.04, 0.02]

SKIP_REASONS = ["closed", "no_receiver", "back_door_blocked", "weather", "out_of_hours", "customer_refused"]

SETTLEMENT_STATUS = ["open", "reconciled", "disputed", "adjusted", "closed"]
SETTLEMENT_STATUS_W = [0.04, 0.18, 0.05, 0.08, 0.65]

DEDUCTION_TYPES = ["shortage", "damages", "expired", "pricing", "stale", "promo", "swell", "other"]
DEDUCTION_TYPE_W = [0.30, 0.18, 0.14, 0.12, 0.10, 0.08, 0.05, 0.03]

DEDUCTION_STATUS = ["open", "matched", "disputed", "paid", "written_off", "chargeback_lost"]
DEDUCTION_STATUS_W = [0.18, 0.22, 0.12, 0.38, 0.07, 0.03]

DISPUTE_REASONS_DSD = [
    "epod_signed_for_full_qty", "store_signed_for_short", "wrong_account_charged",
    "duplicate_claim", "out_of_window", "pricing_error", "swap_not_credited",
]

CATEGORIES_DSD = [
    ("Carbonated Beverages", "CSD"),
    ("Carbonated Beverages", "Energy"),
    ("Salty Snacks", "Chips"),
    ("Salty Snacks", "Pretzels"),
    ("Bakery", "Bread"),
    ("Bakery", "Buns"),
    ("Dairy", "Milk"),
    ("Dairy", "Yogurt"),
    ("Beer & Malt", "Beer"),
    ("Beer & Malt", "Hard Seltzer"),
    ("Confectionery", "Chocolate"),
    ("Confectionery", "Gum"),
    ("Frozen", "Ice Cream"),
    ("Tobacco", "Cigarettes"),
]

BRANDS_DSD = [
    "Pepsi", "Coca-Cola", "Frito-Lay", "Anheuser-Busch", "Coors",
    "Hershey", "Mondelez", "Bimbo Bakeries", "Flowers Foods",
    "Dr Pepper Snapple", "Red Bull", "Monster", "Nestle Waters",
    "Boar's Head", "Sara Lee", "Mars Wrigley",
]

PACK_SIZES_DSD = [
    "12oz can 12pk", "20oz btl", "2L btl", "1.5oz bag", "9.75oz bag",
    "16oz bag", "8ct bar", "20-loaf tray", "12oz btl 6pk", "24oz can",
    "16oz can 4pk", "1gal", "half-gal", "ice-cream pint",
]

HOS_STATUS = ["off_duty", "sleeper", "on_duty", "driving"]
HOS_STATUS_W = [0.30, 0.10, 0.20, 0.40]

HARSH_EVENT = ["harsh_brake", "harsh_accel", "hard_corner", "over_speed"]
HARSH_EVENT_W = [0.40, 0.25, 0.20, 0.15]

# ---------------------------------------------------------------------------
# Generators

def _accounts(ctx, n=2_500):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "account_id": [f"DSDA{i:06d}" for i in range(1, n + 1)],
        "account_name": [f.company() for _ in range(n)],
        "channel": weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "country_iso2": rng.choice(["US", "CA", "MX"], size=n, p=[0.86, 0.09, 0.05]),
        "trade_terms_code": rng.choice(["mixed", "off_invoice_only", "scan_down_only", "edlp_focus"],
                                        size=n, p=[0.55, 0.25, 0.10, 0.10]),
        "status": rng.choice(["active", "active", "active", "inactive"], size=n),
    })


def _outlets(ctx, accounts, n=25_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    sub = accounts.iloc[a_idx].reset_index(drop=True)
    return pd.DataFrame({
        "outlet_id": [f"DSDO{i:07d}" for i in range(1, n + 1)],
        "account_id": sub["account_id"].to_numpy(),
        "gln": [f"{rng.integers(10**12, 10**13):013d}" for _ in range(n)],
        "store_number": [f"{rng.integers(1, 9999):04d}" for _ in range(n)],
        "country_iso2": sub["country_iso2"].to_numpy(),
        "state_region": rng.choice(US_STATES, size=n),
        "postal_code": [f"{rng.integers(10**4, 10**5):05d}" for _ in range(n)],
        "format": weighted_choice(rng, OUTLET_FORMATS, OUTLET_FORMAT_W, n),
        "lat": np.round(rng.uniform(25.0, 49.0, size=n), 6),
        "lng": np.round(rng.uniform(-124.0, -67.0, size=n), 6),
        "status": rng.choice(["active", "active", "active", "remodel", "closed"], size=n),
    })


def _products(ctx, n=600):
    rng = ctx.rng
    cat_idx = rng.integers(0, len(CATEGORIES_DSD), size=n)
    cats = [CATEGORIES_DSD[i] for i in cat_idx]
    list_price = (rng.lognormal(2.4, 0.6, size=n) * 100).astype(np.int64)
    refrigerated = np.array([(c[0] in ("Dairy", "Frozen", "Beer & Malt")) for c in cats])
    return pd.DataFrame({
        "sku_id": [f"DSDS{i:06d}" for i in range(1, n + 1)],
        "gtin": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "brand": rng.choice(BRANDS_DSD, size=n),
        "category": [c[0] for c in cats],
        "subcategory": [c[1] for c in cats],
        "pack_size": rng.choice(PACK_SIZES_DSD, size=n),
        "case_pack_qty": rng.choice([6, 8, 12, 12, 12, 18, 24, 24, 36, 48], size=n).astype("int16"),
        "list_price_cents": list_price,
        "srp_cents": (list_price * rng.uniform(1.20, 1.65, size=n)).astype(np.int64),
        "cost_of_goods_cents": (list_price * rng.uniform(0.45, 0.70, size=n)).astype(np.int64),
        "refrigerated": refrigerated,
        "perishable": refrigerated | np.array([(c[0] in ("Bakery",)) for c in cats]),
        "status": rng.choice(["active", "active", "active", "discontinued", "phasing_in"], size=n),
    })


def _routes(ctx, n=500):
    rng = ctx.rng
    branches = [f"BR{rng.integers(1, 80):03d}" for _ in range(n)]
    veh_class = weighted_choice(rng, VEHICLE_CLASSES, VEHICLE_CLASS_W, n)
    return pd.DataFrame({
        "route_id": [f"RT{i:06d}" for i in range(1, n + 1)],
        "branch_id": branches,
        "route_code": [f"{branches[i][2:].upper()}-{rng.integers(1, 999):03d}" for i in range(n)],
        "route_type": weighted_choice(rng, ROUTE_TYPES, ROUTE_TYPE_W, n),
        "service_days": rng.choice(["MTWHF", "MWF", "TTHS", "MTWHFS", "MTWHFSU"], size=n,
                                    p=[0.34, 0.18, 0.10, 0.30, 0.08]),
        "planned_stops": rng.integers(35, 65, size=n).astype("int16"),
        "planned_miles": np.round(rng.uniform(60, 250, size=n), 2),
        "planned_duration_min": rng.integers(360, 660, size=n),
        "vehicle_class": veh_class,
        "status": rng.choice(["active", "active", "active", "retired"], size=n),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2018-01-01").timestamp()),
                         int(pd.Timestamp("2025-01-01").timestamp()), size=n),
            unit="s"),
        "effective_from": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                         int(pd.Timestamp("2025-12-01").timestamp()), size=n),
            unit="s").date,
        "effective_to": pd.NaT,
    })


def _drivers(ctx, n=500):
    rng = ctx.rng
    f = ctx.faker
    hire_ts = rng.integers(int(pd.Timestamp("2008-01-01").timestamp()),
                            int(pd.Timestamp("2025-06-01").timestamp()), size=n)
    hire_dates = pd.to_datetime(hire_ts, unit="s")
    tenure = (pd.Timestamp("2026-05-11") - hire_dates).days / 365.25
    return pd.DataFrame({
        "driver_id": [f"DR{i:06d}" for i in range(1, n + 1)],
        "branch_id": [f"BR{rng.integers(1, 80):03d}" for _ in range(n)],
        "employee_number": [f"EMP-{rng.integers(10**5, 10**6):06d}" for _ in range(n)],
        "full_name": [f.name() for _ in range(n)],
        "cdl_class": weighted_choice(rng, CDL_CLASSES, CDL_CLASS_W, n),
        "cdl_expiry": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-06-01").timestamp()),
                         int(pd.Timestamp("2030-01-01").timestamp()), size=n),
            unit="s").date,
        "hire_date": hire_dates.date,
        "tenure_years": np.round(tenure, 2),
        "eld_device_id": [f"ELD-{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "home_terminal": [f"BR{rng.integers(1, 80):03d}" for _ in range(n)],
        "pay_class": weighted_choice(rng, PAY_CLASSES, PAY_CLASS_W, n),
        "status": rng.choice(["active", "active", "active", "leave", "terminated"], size=n),
    })


def _vehicles(ctx, n=500):
    rng = ctx.rng
    veh_class = weighted_choice(rng, VEHICLE_CLASSES, VEHICLE_CLASS_W, n)
    mk_idx = rng.integers(0, len(VEHICLE_MAKES), size=n)
    payload = np.where(veh_class == "tractor-trailer", rng.integers(30000, 50000, size=n),
              np.where(veh_class == "bobtail", rng.integers(15000, 26000, size=n),
              np.where(veh_class == "side-bay", rng.integers(12000, 22000, size=n),
              np.where(veh_class == "step-van", rng.integers(6000, 14000, size=n),
                       rng.integers(3000, 8000, size=n)))))
    return pd.DataFrame({
        "vehicle_id": [f"VH{i:06d}" for i in range(1, n + 1)],
        "branch_id": [f"BR{rng.integers(1, 80):03d}" for _ in range(n)],
        "asset_tag": [f"AT-{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "vin": [f"1FUJA{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "make": [VEHICLE_MAKES[i][0] for i in mk_idx],
        "model": [VEHICLE_MAKES[i][1] for i in mk_idx],
        "year": rng.integers(2015, 2026, size=n).astype("int16"),
        "vehicle_class": veh_class,
        "gvwr_lbs": (payload * 1.4).astype(int),
        "payload_lbs": payload.astype(int),
        "bay_count": rng.choice([0, 4, 6, 8, 10, 12], size=n, p=[0.20, 0.10, 0.20, 0.30, 0.15, 0.05]).astype("int16"),
        "refrigerated": rng.random(n) < 0.42,
        "telematics_provider": weighted_choice(rng, TELEMATICS, TELEMATICS_W, n),
        "ifta_jurisdictions": [f'["{rng.choice(US_STATES)}","{rng.choice(US_STATES)}","{rng.choice(US_STATES)}"]'
                                for _ in range(n)],
        "status": rng.choice(["active", "active", "active", "shop", "retired"], size=n),
    })


def _stops(ctx, routes, outlets, service_days=90):
    """One stop per route per service-day per planned stop position."""
    rng = ctx.rng
    n_routes = len(routes)
    avg_stops = 50  # average stops per route per day
    stop_counts = rng.integers(35, 65, size=(n_routes, service_days))
    total = int(stop_counts.sum())

    # Assign route, day, sequence
    route_arr = np.repeat(routes["route_id"].to_numpy(), stop_counts.sum(axis=1))
    # Per-route day expansion
    day_arr = np.empty(total, dtype="datetime64[D]")
    seq_arr = np.empty(total, dtype="int16")
    pos = 0
    base_day = pd.Timestamp("2026-02-09")  # 90-day window ending 2026-05-09
    for r_i in range(n_routes):
        for d in range(service_days):
            n_stops = stop_counts[r_i, d]
            day_arr[pos:pos + n_stops] = (base_day + pd.Timedelta(days=int(d))).to_datetime64().astype("datetime64[D]")
            seq_arr[pos:pos + n_stops] = np.arange(1, n_stops + 1, dtype="int16")
            pos += n_stops

    # Random outlet per stop
    o_idx = rng.integers(0, len(outlets), size=total)
    sub_outlets = outlets.iloc[o_idx].reset_index(drop=True)

    # Time windows — base 6 AM, 7-min cadence
    base_minutes = (seq_arr - 1) * 7 + 360
    arrival_jitter = rng.integers(-5, 30, size=total)
    actual_minutes = base_minutes + arrival_jitter
    dwell = rng.integers(4, 25, size=total)

    day_ts = pd.to_datetime(day_arr)
    planned_arrival = day_ts + pd.to_timedelta(base_minutes, unit="m")
    actual_arrival = day_ts + pd.to_timedelta(actual_minutes, unit="m")
    planned_departure = planned_arrival + pd.to_timedelta(dwell, unit="m")
    actual_departure = actual_arrival + pd.to_timedelta(dwell, unit="m")

    status = weighted_choice(rng, STOP_STATUS, STOP_STATUS_W, total)
    skip_mask = status == "skipped"
    skip_reason = np.where(skip_mask, rng.choice(SKIP_REASONS, size=total), None)
    actual_seq = np.where(skip_mask, None, seq_arr + rng.integers(-2, 3, size=total))

    return pd.DataFrame({
        "stop_id": [f"ST{i:010d}" for i in range(1, total + 1)],
        "route_id": route_arr,
        "route_day": day_arr,
        "outlet_id": sub_outlets["outlet_id"].to_numpy(),
        "gln": sub_outlets["gln"].to_numpy(),
        "planned_sequence": seq_arr,
        "actual_sequence": actual_seq,
        "planned_arrival": planned_arrival,
        "actual_arrival": actual_arrival,
        "planned_departure": planned_departure,
        "actual_departure": actual_departure,
        "dwell_minutes": dwell.astype(int),
        "status": status,
        "skip_reason": skip_reason,
        "lat": sub_outlets["lat"].to_numpy(),
        "lng": sub_outlets["lng"].to_numpy(),
        "presell_flag": rng.random(total) < 0.34,
    })


def _orders(ctx, stops):
    """One order per non-skipped stop (some have presell pre-order + delivery)."""
    rng = ctx.rng
    eligible = stops[~stops["status"].isin(["skipped", "scheduled"])].reset_index(drop=True)
    n = len(eligible)
    return pd.DataFrame({
        "order_id": [f"OR{i:010d}" for i in range(1, n + 1)],
        "stop_id": eligible["stop_id"].to_numpy(),
        "outlet_id": eligible["outlet_id"].to_numpy(),
        "order_type": np.where(eligible["presell_flag"].to_numpy(),
                                rng.choice(["presell", "deliver"], p=[0.55, 0.45], size=n),
                                weighted_choice(rng, ORDER_TYPES, ORDER_TYPE_W, n)),
        "order_date": pd.to_datetime(eligible["route_day"]).dt.date,
        "requested_delivery_date": pd.to_datetime(eligible["route_day"]).dt.date,
        "account_id": [f"DSDA{rng.integers(1, 2500):06d}" for _ in range(n)],
        "salesman_id": [f"SR{rng.integers(1, 700):05d}" for _ in range(n)],
        "total_cases": rng.integers(2, 80, size=n),
        "total_units": rng.integers(20, 1500, size=n),
        "gross_amount_cents": (rng.lognormal(7.5, 0.9, size=n) * 100).astype(np.int64),
        "discount_amount_cents": (rng.lognormal(5.5, 1.0, size=n) * 100).astype(np.int64),
        "net_amount_cents": (rng.lognormal(7.4, 0.9, size=n) * 100).astype(np.int64),
        "tax_amount_cents": (rng.lognormal(4.5, 1.0, size=n) * 100).astype(np.int64),
        "payment_terms": weighted_choice(rng, PAYMENT_TERMS, PAYMENT_TERMS_W, n),
        "status": weighted_choice(rng, ORDER_STATUS, ORDER_STATUS_W, n),
        "created_at": pd.to_datetime(eligible["actual_arrival"]),
    })


def _order_lines(ctx, orders, products, avg_lines=10):
    """About 10 SKU lines per order (target ~22.5M lines for 90-day demo)."""
    rng = ctx.rng
    n_orders = len(orders)
    counts = rng.integers(3, avg_lines * 2, size=n_orders)
    n = int(counts.sum())
    order_idx = np.repeat(np.arange(n_orders), counts)
    sub_orders = orders.iloc[order_idx].reset_index(drop=True)
    p_idx = rng.integers(0, len(products), size=n)
    sub_products = products.iloc[p_idx].reset_index(drop=True)

    case_pack = sub_products["case_pack_qty"].to_numpy().astype(int)
    ordered_cases = rng.integers(1, 10, size=n).astype(int)
    ordered_units = (ordered_cases * case_pack).astype(int)
    delivered_units = (ordered_units * rng.uniform(0.85, 1.0, size=n)).astype(int)
    delivered_cases = (delivered_units // np.maximum(1, case_pack)).astype(int)
    returned_units = (ordered_units * rng.uniform(0.0, 0.04, size=n)).astype(int)
    short_units = (ordered_units - delivered_units - returned_units).clip(min=0).astype(int)

    unit_price = sub_products["list_price_cents"].to_numpy().astype(np.int64)
    extended = (delivered_units * unit_price).astype(np.int64)

    return pd.DataFrame({
        "order_line_id": [f"OL{i:011d}" for i in range(1, n + 1)],
        "order_id": sub_orders["order_id"].to_numpy(),
        "sku_id": sub_products["sku_id"].to_numpy(),
        "gtin": sub_products["gtin"].to_numpy(),
        "ordered_units": ordered_units,
        "ordered_cases": ordered_cases,
        "delivered_units": delivered_units,
        "delivered_cases": delivered_cases,
        "returned_units": returned_units,
        "short_units": short_units,
        "unit_price_cents": unit_price,
        "extended_amount_cents": extended,
        "promo_tactic_id": np.where(rng.random(n) < 0.20,
                                     [f"TAC{rng.integers(1, 800_000):09d}" for _ in range(n)],
                                     None),
        "lot_number": [f"LOT-{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "expiry_date": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-05-15").timestamp()),
                         int(pd.Timestamp("2027-12-31").timestamp()), size=n),
            unit="s").date,
        "route_load_position": [f"B{rng.integers(1, 12):02d}-S{rng.integers(1, 24):02d}" for _ in range(n)],
    })


def _settlements(ctx, routes, drivers, vehicles, stops):
    """One settlement per (route, route_day) with driver/vehicle assigned."""
    rng = ctx.rng
    days = pd.to_datetime(stops["route_day"]).drop_duplicates().sort_values().to_numpy()
    n_routes = len(routes)
    pairs = []
    for d in days:
        for r in routes["route_id"].to_numpy():
            pairs.append((r, d))
    n = len(pairs)
    route_arr = np.array([p[0] for p in pairs])
    day_arr = np.array([p[1] for p in pairs])

    d_idx = rng.integers(0, len(drivers), size=n)
    v_idx = rng.integers(0, len(vehicles), size=n)
    invoiced = (rng.lognormal(9.0, 0.7, size=n) * 100).astype(np.int64)
    cash = (invoiced * rng.uniform(0.10, 0.50, size=n)).astype(np.int64)
    check = (invoiced * rng.uniform(0.05, 0.30, size=n)).astype(np.int64)
    eft = (invoiced * rng.uniform(0.10, 0.50, size=n)).astype(np.int64)
    charge = invoiced - cash - check - eft
    charge = np.where(charge < 0, 0, charge)
    returns_credit = (invoiced * rng.uniform(0.0, 0.05, size=n)).astype(np.int64)
    spoils_credit = (invoiced * rng.uniform(0.0, 0.02, size=n)).astype(np.int64)
    expected_total = invoiced - returns_credit - spoils_credit
    actual_total = cash + check + eft + charge
    variance = (actual_total - expected_total).astype(np.int64)
    status = weighted_choice(rng, SETTLEMENT_STATUS, SETTLEMENT_STATUS_W, n)
    closed_at = pd.to_datetime(day_arr) + pd.to_timedelta(rng.integers(8, 14, size=n), unit="h")

    return pd.DataFrame({
        "settlement_id": [f"SET{i:010d}" for i in range(1, n + 1)],
        "route_id": route_arr,
        "driver_id": drivers["driver_id"].to_numpy()[d_idx],
        "vehicle_id": vehicles["vehicle_id"].to_numpy()[v_idx],
        "settlement_date": pd.to_datetime(day_arr).date,
        "total_invoiced_cents": invoiced,
        "total_collected_cash_cents": cash,
        "total_collected_check_cents": check,
        "total_collected_eft_cents": eft,
        "total_charge_account_cents": charge,
        "returns_credit_cents": returns_credit,
        "spoilage_credit_cents": spoils_credit,
        "variance_cents": variance,
        "variance_reason": np.where(np.abs(variance) > 2500,
                                     rng.choice(["short_collection", "miskey_price", "unrecorded_return", "cage_count_off"], size=n),
                                     None),
        "status": status,
        "closed_at": closed_at,
        "approved_by": [f"sup_{rng.integers(1, 250):03d}" for _ in range(n)],
    })


def _epod_events(ctx, orders, stops, capture_pct=0.93):
    rng = ctx.rng
    delivered = orders[orders["status"].isin(["delivered", "invoiced"])].reset_index(drop=True)
    keep_mask = rng.random(len(delivered)) < capture_pct
    sub = delivered[keep_mask].reset_index(drop=True)
    n = len(sub)
    sub_stops = stops.set_index("stop_id").loc[sub["stop_id"].to_numpy()].reset_index(drop=True)
    signed_at = pd.to_datetime(sub_stops["actual_departure"]).to_numpy() + pd.to_timedelta(rng.integers(-300, 60, size=n), unit="s")
    return pd.DataFrame({
        "epod_id": [f"EP{i:010d}" for i in range(1, n + 1)],
        "stop_id": sub["stop_id"].to_numpy(),
        "order_id": sub["order_id"].to_numpy(),
        "signed_at": signed_at,
        "signed_by": [f"Receiver-{rng.integers(1, 99999):05d}" for _ in range(n)],
        "signature_image_uri": [f"s3://dsd-epod/sig/{rng.integers(10**9, 10**10):010d}.png" for _ in range(n)],
        "photo_uri": [f"s3://dsd-epod/photo/{rng.integers(10**9, 10**10):010d}.jpg" for _ in range(n)],
        "geo_lat": sub_stops["lat"].to_numpy(),
        "geo_lng": sub_stops["lng"].to_numpy(),
        "device_id": [f"{rng.choice(['HON-CN80','HON-CT45','ZBR-TC78','ZBR-MC9300'])}-{rng.integers(10**5, 10**6):06d}" for _ in range(n)],
        "edi_895_doc_id": [f"EDI895-{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
    })


def _perfect_store_audits(ctx, stops, n=100_000):
    rng = ctx.rng
    s_idx = rng.integers(0, len(stops), size=n)
    sub = stops.iloc[s_idx].reset_index(drop=True)
    distribution = np.round(rng.normal(82, 12, size=n).clip(0, 100), 2)
    cooler = np.round(rng.normal(35, 10, size=n).clip(0, 100), 2)
    plano = np.round(rng.normal(78, 14, size=n).clip(0, 100), 2)
    price = np.round(rng.normal(88, 8, size=n).clip(0, 100), 2)
    promo = np.round(rng.normal(70, 18, size=n).clip(0, 100), 2)
    fresh = np.round(rng.normal(85, 10, size=n).clip(0, 100), 2)
    score = np.round(0.20 * distribution + 0.20 * cooler + 0.20 * plano + 0.10 * price + 0.20 * promo + 0.10 * fresh, 2)
    return pd.DataFrame({
        "audit_id": [f"AU{i:010d}" for i in range(1, n + 1)],
        "stop_id": sub["stop_id"].to_numpy(),
        "outlet_id": sub["outlet_id"].to_numpy(),
        "audit_date": pd.to_datetime(sub["route_day"]).dt.date,
        "auditor_id": [f"AUD{rng.integers(1, 700):05d}" for _ in range(n)],
        "distribution_score": distribution,
        "share_of_cooler_pct": cooler,
        "planogram_compliance_pct": plano,
        "price_compliance_pct": price,
        "promo_compliance_pct": promo,
        "freshness_score": fresh,
        "oos_count": rng.integers(0, 8, size=n).astype("int16"),
        "perfect_store_score": score,
        "photo_uri": [f"s3://dsd-audits/{rng.integers(10**9, 10**10):010d}.jpg" for _ in range(n)],
        "notes": rng.choice([
            None, "cooler reset OK", "rear-facing tags", "competitor end-cap encroachment",
            "out-of-stock zone observed", "expired SKU pulled",
        ], size=n),
    })


def _route_telemetry(ctx, vehicles, drivers, n=5_000_000):
    rng = ctx.rng
    v_idx = rng.integers(0, len(vehicles), size=n)
    d_idx = rng.integers(0, len(drivers), size=n)
    observed = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-09").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    speed = np.round(rng.uniform(0, 65, size=n), 2)
    harsh_mask = rng.random(n) < 0.02
    harsh_evt = np.where(harsh_mask, weighted_choice(rng, HARSH_EVENT, HARSH_EVENT_W, n), None)
    return pd.DataFrame({
        "telemetry_id": [f"TM{i:012d}" for i in range(1, n + 1)],
        "vehicle_id": vehicles["vehicle_id"].to_numpy()[v_idx],
        "driver_id": drivers["driver_id"].to_numpy()[d_idx],
        "observed_at": observed,
        "lat": np.round(rng.uniform(25.0, 49.0, size=n), 6),
        "lng": np.round(rng.uniform(-124.0, -67.0, size=n), 6),
        "speed_mph": speed,
        "heading_deg": rng.integers(0, 360, size=n).astype("int16"),
        "odometer_miles": np.round(rng.uniform(10_000, 350_000, size=n), 2),
        "fuel_pct": np.round(rng.uniform(5, 100, size=n), 2),
        "ignition_on": rng.random(n) < 0.86,
        "hos_status": weighted_choice(rng, HOS_STATUS, HOS_STATUS_W, n),
        "harsh_event_type": harsh_evt,
    })


def _deductions(ctx, orders, n=50_000):
    rng = ctx.rng
    o_idx = rng.integers(0, len(orders), size=n)
    sub = orders.iloc[o_idx].reset_index(drop=True)
    amount = (rng.lognormal(6.5, 1.4, size=n) * 100).astype(np.int64)
    status = weighted_choice(rng, DEDUCTION_STATUS, DEDUCTION_STATUS_W, n)
    open_amount = np.where(np.isin(status, ["open", "matched", "disputed"]), amount, 0).astype(np.int64)
    opened = pd.to_datetime(sub["order_date"]) + pd.to_timedelta(rng.integers(7, 60, size=n), unit="D")
    aging = (pd.Timestamp("2026-05-09") - opened).dt.days.clip(lower=0).astype(int)
    epod_evidence = np.where(rng.random(n) < 0.85,
                              [f"s3://dsd-epod/photo/{rng.integers(10**9, 10**10):010d}.jpg" for _ in range(n)],
                              None)
    resolved_mask = np.isin(status, ["paid", "written_off", "chargeback_lost"])
    resolved_at = np.where(resolved_mask,
                            opened + pd.to_timedelta(rng.integers(5, 90, size=n), unit="D"),
                            np.datetime64("NaT"))
    return pd.DataFrame({
        "deduction_id": [f"DD{i:09d}" for i in range(1, n + 1)],
        "account_id": sub["account_id"].to_numpy(),
        "order_id": sub["order_id"].to_numpy(),
        "stop_id": sub["stop_id"].to_numpy(),
        "claim_number": [f"CLM-{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
        "deduction_type": weighted_choice(rng, DEDUCTION_TYPES, DEDUCTION_TYPE_W, n),
        "amount_cents": amount,
        "open_amount_cents": open_amount,
        "opened_date": opened.dt.date,
        "aging_days": aging,
        "status": status,
        "dispute_reason": np.where(status == "disputed",
                                    rng.choice(DISPUTE_REASONS_DSD, size=n), None),
        "epod_evidence_uri": epod_evidence,
        "resolution_date": pd.Series(resolved_at).where(pd.Series(resolved_at).notna(), pd.NaT).dt.date,
    })


# ---------------------------------------------------------------------------
def generate(seed=42, service_days=90, telemetry_rows=5_000_000):
    ctx = make_context(seed)
    print("  generating accounts...")
    accounts = _accounts(ctx)
    print("  generating outlets...")
    outlets = _outlets(ctx, accounts)
    print("  generating products...")
    products = _products(ctx)
    print("  generating routes (500)...")
    routes = _routes(ctx)
    print("  generating drivers (500)...")
    drivers = _drivers(ctx)
    print("  generating vehicles (500)...")
    vehicles = _vehicles(ctx)
    print(f"  generating stops (~{500*50*service_days/1e6:.1f}M)...")
    stops = _stops(ctx, routes, outlets, service_days=service_days)
    print(f"  generating orders ({len(stops):,} stops → ~{len(stops)*0.94:.0f} orders)...")
    orders = _orders(ctx, stops)
    print(f"  generating order lines (~{len(orders)*10/1e6:.1f}M)...")
    order_lines = _order_lines(ctx, orders, products)
    print("  generating settlements (route × day)...")
    settlements = _settlements(ctx, routes, drivers, vehicles, stops)
    print("  generating epod events...")
    epods = _epod_events(ctx, orders, stops)
    print("  generating perfect-store audits (100k)...")
    audits = _perfect_store_audits(ctx, stops)
    print(f"  generating route telemetry ({telemetry_rows:,} rows)...")
    telemetry = _route_telemetry(ctx, vehicles, drivers, n=telemetry_rows)
    print("  generating deductions (50k)...")
    deductions = _deductions(ctx, orders)

    tables = {
        "account": accounts,
        "outlet": outlets,
        "product": products,
        "route": routes,
        "driver": drivers,
        "vehicle": vehicles,
        "stop": stops,
        "dsd_order": orders,
        "dsd_order_line": order_lines,
        "settlement": settlements,
        "epod_event": epods,
        "perfect_store_audit": audits,
        "route_telemetry": telemetry,
        "deduction": deductions,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--service-days", type=int, default=90,
                   help="Number of route service-days to simulate (default 90 for ~22M order lines).")
    p.add_argument("--telemetry-rows", type=int, default=5_000_000,
                   help="Override route_telemetry row count for faster local runs.")
    args = p.parse_args()
    tables = generate(args.seed, service_days=args.service_days, telemetry_rows=args.telemetry_rows)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
