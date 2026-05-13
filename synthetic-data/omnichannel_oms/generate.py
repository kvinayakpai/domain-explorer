"""
Synthetic Omnichannel Order Management data —
Manhattan Active OM / IBM Sterling OMS / Salesforce OMS / Shopify /
Oracle ROMS / Kibo / Fluent Commerce / Aptos / Logiwa.

Entities (>=10):
  customer, location, product, inventory_position, sourcing_rule, oms_order,
  order_line, allocation, fulfillment_event, shipment, return_authorization.

Realism:
  - 100k orders × ~3 lines avg over 90 days; ~30 stores + 5 DCs + 3 dark stores.
  - 50k inventory positions (2k SKUs × ~25 nodes).
  - ~200k fulfillment events covering pick → pack → ship → deliver / pickup.
  - ~30k shipments; ~10k returns.
  - Lifecycle distributions reflect Manhattan / Sterling published OMS reports:
      * 92% of orders close successfully, 4% cancel, 4% return.
      * ~28% of orders source from a store (ship-from-store) when DC is dry.
      * ~22% of orders are BOPIS in apparel/general merch deployments.
      * 12% of multi-line orders split across nodes.
  - All large-range integer IDs use the int64-safe pattern from
    capital_markets/generate.py (rng.integers + zero-padded format string).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table  # noqa: E402

SUBDOMAIN = "omnichannel_oms"

# -----------------------------------------------------------------------------
COUNTRIES = ["US", "GB", "DE", "FR", "JP", "CA", "AU", "SG", "NL", "IT", "ES", "MX"]
TIMEZONES = ["America/New_York", "America/Chicago", "America/Los_Angeles",
             "Europe/London", "Europe/Berlin", "Asia/Tokyo", "Australia/Sydney"]
LOCATION_TYPES = ["store", "dc", "dark_store", "drop_ship", "partner", "locker"]
LOCATION_TYPE_W = [0.78, 0.10, 0.06, 0.03, 0.02, 0.01]

CAPTURE_CHANNELS = ["web", "app", "store_pos", "kiosk", "call_center", "marketplace", "agent"]
CAPTURE_CHANNEL_W = [0.42, 0.28, 0.13, 0.04, 0.04, 0.07, 0.02]

FULFILLMENT_METHODS = ["ship_to_home", "bopis", "sfs", "curbside", "delivery", "drop_ship", "same_day"]
FULFILLMENT_METHOD_W = [0.46, 0.22, 0.12, 0.06, 0.06, 0.05, 0.03]

ORDER_STATUSES = [
    "captured", "sourced", "in_fulfillment", "partial_shipped",
    "shipped", "delivered", "picked_up", "cancelled", "returned",
]
ORDER_STATUS_W = [0.02, 0.02, 0.04, 0.04, 0.10, 0.50, 0.20, 0.04, 0.04]

PAYMENT_STATUSES = ["authorized", "captured", "partial", "refunded", "voided"]
PAYMENT_STATUS_W = [0.04, 0.84, 0.04, 0.06, 0.02]

LINE_STATUSES = [
    "open", "sourced", "allocated", "picked", "packed",
    "shipped", "delivered", "picked_up", "cancelled", "substituted", "returned",
]
LINE_STATUS_W = [0.02, 0.02, 0.04, 0.04, 0.04, 0.10, 0.46, 0.18, 0.04, 0.02, 0.04]

EVENT_TYPES = [
    "pick_started", "pick_complete", "substitution", "short_pick",
    "pack", "label", "ship", "in_transit", "out_for_delivery", "delivered",
    "pickup_ready", "pickup_complete", "cancel", "reallocate",
    "return_initiated", "return_received", "refund_issued",
]
EVENT_TYPE_W = [0.10, 0.10, 0.02, 0.02, 0.08, 0.07, 0.10, 0.12, 0.08, 0.10,
                0.06, 0.05, 0.03, 0.02, 0.02, 0.02, 0.01]

ACTOR_ROLES = ["system", "store_associate", "warehouse_picker", "carrier", "customer"]
ACTOR_ROLE_W = [0.50, 0.18, 0.12, 0.16, 0.04]

CARRIERS = ["fedex", "ups", "usps", "dhl", "store_courier", "ontrac", "lasership", "same_day"]
CARRIER_W = [0.32, 0.28, 0.18, 0.06, 0.06, 0.05, 0.03, 0.02]

SERVICE_LEVELS = ["ground", "2day", "next_day", "same_day", "economy", "home_delivery"]
SERVICE_LEVEL_W = [0.55, 0.18, 0.08, 0.04, 0.10, 0.05]

SHIPMENT_STATUSES = ["label_created", "in_transit", "out_for_delivery", "delivered", "exception", "returned"]
SHIPMENT_STATUS_W = [0.02, 0.06, 0.04, 0.85, 0.02, 0.01]

RETURN_REASONS = ["wrong_item", "defective", "too_small", "too_large", "did_not_like",
                  "late", "damaged_in_transit", "other"]
RETURN_REASON_W = [0.07, 0.10, 0.18, 0.16, 0.30, 0.05, 0.08, 0.06]

RETURN_METHODS = ["in_store", "mail", "carrier_pickup", "locker"]
RETURN_METHOD_W = [0.50, 0.38, 0.07, 0.05]

REFUND_METHODS = ["original_tender", "store_credit", "gift_card", "exchange"]
REFUND_METHOD_W = [0.78, 0.10, 0.06, 0.06]

RESTOCK_OUTCOMES = ["restocked", "damaged", "donated", "destroyed", "return_to_vendor"]
RESTOCK_OUTCOME_W = [0.74, 0.12, 0.04, 0.04, 0.06]

SOURCE_SYSTEMS = ["Manhattan", "Sterling", "SFOMS", "Shopify", "RMS", "Kibo", "Fluent", "WMS"]
SOURCE_SYSTEM_W = [0.22, 0.18, 0.16, 0.16, 0.10, 0.08, 0.06, 0.04]

CATEGORIES = ["apparel", "footwear", "electronics", "home", "beauty", "sporting", "auto", "toys", "grocery"]


# -----------------------------------------------------------------------------
def _customers(ctx, n=120_000):
    rng = ctx.rng
    return pd.DataFrame({
        "customer_id":       [f"CUS{i:09d}" for i in range(1, n + 1)],
        "golden_record_id":  [f"GRC{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "email_hash":        [f"sha256:{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "phone_hash":        [f"sha256:{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
        "loyalty_id":        np.where(rng.random(n) < 0.62,
                                       [f"LYL{rng.integers(10**7, 10**8):08d}" for _ in range(n)], None),
        "home_country_iso2": rng.choice(COUNTRIES, size=n, p=[0.55, 0.10, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03, 0.03, 0.03, 0.02]),
        "created_at":        pd.to_datetime(
            rng.integers(int(pd.Timestamp("2022-01-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
        "status":            weighted_choice(rng, ["active", "merged", "suppressed"], [0.96, 0.03, 0.01], n),
    })


def _locations(ctx, n_stores=30, n_dcs=5, n_dark=3, n_locker=2):
    rng = ctx.rng
    rows = []
    # Stores
    for i in range(1, n_stores + 1):
        rows.append({
            "location_id": f"STR{i:03d}",
            "gln": f"{rng.integers(10**12, 10**13):013d}",
            "name": f"Store #{i}",
            "location_type": "store",
            "country_iso2": rng.choice(["US", "GB", "DE", "FR", "CA"], p=[0.6, 0.15, 0.1, 0.1, 0.05]),
            "region": rng.choice(["NE", "SE", "MW", "W", "EU-N", "EU-S"]),
            "timezone": rng.choice(TIMEZONES),
            "lat": float(np.round(rng.uniform(25.0, 55.0), 6)),
            "lon": float(np.round(rng.uniform(-125.0, 25.0), 6)),
            "bopis_enabled": True,
            "ship_from_enabled": rng.random() < 0.85,
            "pick_capacity_per_hour": int(rng.integers(15, 80)),
            "status": "active",
        })
    # DCs
    for i in range(1, n_dcs + 1):
        rows.append({
            "location_id": f"DC{i:02d}",
            "gln": f"{rng.integers(10**12, 10**13):013d}",
            "name": f"Distribution Center #{i}",
            "location_type": "dc",
            "country_iso2": rng.choice(["US", "GB", "DE"], p=[0.6, 0.2, 0.2]),
            "region": rng.choice(["NE", "SE", "MW", "W", "EU"]),
            "timezone": rng.choice(TIMEZONES),
            "lat": float(np.round(rng.uniform(25.0, 55.0), 6)),
            "lon": float(np.round(rng.uniform(-125.0, 25.0), 6)),
            "bopis_enabled": False,
            "ship_from_enabled": True,
            "pick_capacity_per_hour": int(rng.integers(800, 3000)),
            "status": "active",
        })
    # Dark stores
    for i in range(1, n_dark + 1):
        rows.append({
            "location_id": f"DRK{i:02d}",
            "gln": f"{rng.integers(10**12, 10**13):013d}",
            "name": f"Dark Store #{i}",
            "location_type": "dark_store",
            "country_iso2": "US",
            "region": rng.choice(["NE", "W", "MW"]),
            "timezone": rng.choice(TIMEZONES),
            "lat": float(np.round(rng.uniform(25.0, 49.0), 6)),
            "lon": float(np.round(rng.uniform(-125.0, -70.0), 6)),
            "bopis_enabled": False,
            "ship_from_enabled": True,
            "pick_capacity_per_hour": int(rng.integers(150, 600)),
            "status": "active",
        })
    # Lockers
    for i in range(1, n_locker + 1):
        rows.append({
            "location_id": f"LKR{i:02d}",
            "gln": f"{rng.integers(10**12, 10**13):013d}",
            "name": f"Locker Hub #{i}",
            "location_type": "locker",
            "country_iso2": "US",
            "region": "W",
            "timezone": "America/Los_Angeles",
            "lat": float(np.round(rng.uniform(33.0, 49.0), 6)),
            "lon": float(np.round(rng.uniform(-125.0, -100.0), 6)),
            "bopis_enabled": True,
            "ship_from_enabled": False,
            "pick_capacity_per_hour": 0,
            "status": "active",
        })
    return pd.DataFrame(rows)


def _products(ctx, n=2_000):
    rng = ctx.rng
    return pd.DataFrame({
        "product_id":  [f"PRD{i:06d}" for i in range(1, n + 1)],
        "gtin":        [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "sku":         [f"SKU-{rng.integers(10**5, 10**6):06d}" for _ in range(n)],
        "name":        [f"Product {i}" for i in range(1, n + 1)],
        "category_id": rng.choice(CATEGORIES, size=n),
        "hazmat_flag": rng.random(n) < 0.04,
        "weight_grams":             rng.integers(50, 8000, size=n),
        "dimensional_weight_grams": rng.integers(80, 12000, size=n),
        "pack_type":   rng.choice(["each", "inner", "case"], p=[0.85, 0.10, 0.05], size=n),
        "status":      weighted_choice(rng, ["active", "discontinued", "seasonal"], [0.90, 0.06, 0.04], n),
    })


def _inventory_positions(ctx, locations, products, n=50_000):
    rng = ctx.rng
    n = min(n, len(locations) * len(products))
    loc_idx = rng.integers(0, len(locations), size=n)
    prod_idx = rng.integers(0, len(products), size=n)

    # Different node types carry different inventory profiles.
    loc_types = locations["location_type"].to_numpy()[loc_idx]
    base_qty = np.where(loc_types == "dc",
                        rng.integers(50, 1500, size=n),
                        np.where(loc_types == "dark_store",
                                 rng.integers(20, 400, size=n),
                                 rng.integers(0, 60, size=n)))
    on_hand = base_qty.astype(np.int64)
    allocated = (on_hand * rng.uniform(0.0, 0.3, size=n)).astype(np.int64)
    in_transit = rng.integers(0, 50, size=n).astype(np.int64)
    safety = (on_hand * rng.uniform(0.0, 0.15, size=n)).astype(np.int64)
    atp = (on_hand - allocated - safety).clip(min=0)

    return pd.DataFrame({
        "position_id": [f"INV{i:010d}" for i in range(1, n + 1)],
        "location_id": locations["location_id"].to_numpy()[loc_idx],
        "product_id":  products["product_id"].to_numpy()[prod_idx],
        "on_hand_units":          on_hand,
        "allocated_units":        allocated,
        "in_transit_units":       in_transit,
        "reserved_safety_units":  safety,
        "atp_units":              atp,
        "source_system":          weighted_choice(rng, SOURCE_SYSTEMS, SOURCE_SYSTEM_W, n),
        "as_of_ts": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-02-08").timestamp()),
                         int(pd.Timestamp("2026-05-09").timestamp()), size=n),
            unit="s"),
        "refresh_lag_seconds":    rng.integers(0, 600, size=n),
    })


def _sourcing_rules(ctx, n=24):
    rng = ctx.rng
    names = [
        "primary_dc_first", "store_clearance_pull", "min_split_shipment",
        "fastest_promise", "lowest_cost", "carrier_capacity_balance",
        "hazmat_dc_only", "regional_proximity", "weekend_dc_skip",
        "bopis_local_only", "drop_ship_long_tail", "ground_only_for_economy",
        "premium_member_priority", "weight_based_dc_split", "dark_store_preferred_apparel",
        "locker_eligible_small_pkg", "same_day_geo_radius", "vendor_drop_ship_fallback",
        "endless_aisle_chain_pool", "store_capacity_throttle", "evening_no_pick",
        "next_day_air_premium", "single_node_consolidate", "drop_to_locker_30km",
    ]
    cost_w   = rng.uniform(0.0, 1.0, size=n)
    speed_w  = rng.uniform(0.0, 1.0, size=n)
    cap_w    = rng.uniform(0.0, 1.0, size=n)
    clear_w  = rng.uniform(0.0, 1.0, size=n)
    return pd.DataFrame({
        "rule_id":   [f"RUL{i:04d}" for i in range(1, n + 1)],
        "rule_name": names[:n],
        "priority":  rng.integers(1, 100, size=n).astype(np.int16),
        "condition_json": [
            '{"channel":"web","weight_grams":{"lt":2000}}'
            if i % 4 == 0 else
            '{"hazmat_flag":false,"region":"NE"}'
            if i % 4 == 1 else
            '{"fulfillment_method":"bopis","store_capacity":{"gt":10}}'
            if i % 4 == 2 else
            '{"clearance_age_days":{"gt":120}}'
            for i in range(n)
        ],
        "cost_weight":           np.round(cost_w / (cost_w + speed_w + cap_w + clear_w), 4),
        "speed_weight":          np.round(speed_w / (cost_w + speed_w + cap_w + clear_w), 4),
        "capacity_weight":       np.round(cap_w / (cost_w + speed_w + cap_w + clear_w), 4),
        "clearance_pull_weight": np.round(clear_w / (cost_w + speed_w + cap_w + clear_w), 4),
        "effective_from": pd.Timestamp("2025-12-01"),
        "effective_to":   pd.Timestamp("2026-12-31"),
        "status":         "active",
    })


def _orders(ctx, customers, locations, n=100_000):
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    cap_loc_choice = rng.random(n) < 0.18  # 18% of orders captured at a store endpoint
    store_locs = locations[locations["location_type"] == "store"]["location_id"].to_numpy()
    cap_loc_id = np.where(cap_loc_choice,
                          rng.choice(store_locs, size=n),
                          None)

    captured = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-08").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    promise_offset_h = rng.integers(24, 168, size=n)
    promise = captured + pd.to_timedelta(promise_offset_h, unit="h")

    line_count = np.clip(rng.poisson(2.5, size=n) + 1, 1, 12)  # avg ~3 lines

    subtotal = (rng.lognormal(4.4, 1.0, size=n) * 100).astype(np.int64)
    tax = (subtotal * rng.uniform(0.0, 0.20, size=n)).astype(np.int64)
    shipping = rng.choice([0, 499, 799, 1299, 2499], size=n).astype(np.int64)
    discount = (subtotal * rng.uniform(0.0, 0.20, size=n)).astype(np.int64)
    total = subtotal + tax + shipping - discount
    total = np.clip(total, 100, None)

    status = weighted_choice(rng, ORDER_STATUSES, ORDER_STATUS_W, n)
    closed_offset_h = rng.integers(0, 14 * 24, size=n)
    closed = np.where(np.isin(status, ["delivered", "picked_up", "cancelled", "returned"]),
                      captured + pd.to_timedelta(closed_offset_h, unit="h"),
                      np.datetime64("NaT"))

    return pd.DataFrame({
        "order_id":             [f"ORD{i:010d}" for i in range(1, n + 1)],
        "customer_id":          customers["customer_id"].to_numpy()[c_idx],
        "capture_channel":      weighted_choice(rng, CAPTURE_CHANNELS, CAPTURE_CHANNEL_W, n),
        "capture_location_id":  cap_loc_id,
        "order_total_minor":    total,
        "currency":             rng.choice(["USD", "EUR", "GBP", "JPY", "CAD", "AUD"],
                                            p=[0.62, 0.13, 0.10, 0.05, 0.05, 0.05], size=n),
        "tax_minor":            tax,
        "shipping_minor":       shipping,
        "discount_minor":       discount,
        "payment_status":       weighted_choice(rng, PAYMENT_STATUSES, PAYMENT_STATUS_W, n),
        "order_status":         status,
        "promise_delivery_ts":  promise,
        "captured_at":          captured,
        "closed_at":            closed,
        "_line_count":          line_count,           # internal helper for line generation
    })


def _order_lines(ctx, orders, products, locations):
    rng = ctx.rng
    line_counts = orders["_line_count"].to_numpy()
    total_lines = int(line_counts.sum())
    print(f"    expanding {len(orders):,} orders into {total_lines:,} lines...")

    order_ids = np.repeat(orders["order_id"].to_numpy(), line_counts)
    line_seq = np.concatenate([np.arange(1, lc + 1) for lc in line_counts]).astype(np.int16)

    n = total_lines
    p_idx = rng.integers(0, len(products), size=n)
    qty = np.clip(rng.poisson(1.2, size=n) + 1, 1, 8).astype(np.int64)
    unit_price = (rng.lognormal(3.2, 0.9, size=n) * 100).astype(np.int64).clip(min=99)
    line_total = unit_price * qty

    method = weighted_choice(rng, FULFILLMENT_METHODS, FULFILLMENT_METHOD_W, n)
    bopis_mask = (method == "bopis") | (method == "curbside")
    store_locs = locations[locations["location_type"] == "store"]["location_id"].to_numpy()
    requested_loc = np.where(bopis_mask,
                             rng.choice(store_locs, size=n),
                             None)

    line_status = weighted_choice(rng, LINE_STATUSES, LINE_STATUS_W, n)
    sub_for = np.where(line_status == "substituted",
                       np.array([f"OLN{rng.integers(1, total_lines):010d}" for _ in range(n)]),
                       None)

    return pd.DataFrame({
        "order_line_id":             [f"OLN{i:010d}" for i in range(1, n + 1)],
        "order_id":                  order_ids,
        "product_id":                products["product_id"].to_numpy()[p_idx],
        "line_number":               line_seq,
        "quantity":                  qty,
        "unit_price_minor":          unit_price,
        "line_total_minor":          line_total,
        "fulfillment_method":        method,
        "requested_location_id":     requested_loc,
        "line_status":               line_status,
        "substitution_for_line_id":  sub_for,
    })


def _allocations(ctx, order_lines, locations, sourcing_rules):
    rng = ctx.rng
    # Most lines get an allocation; cancelled/open ones do not.
    eligible_mask = ~order_lines["line_status"].isin(["open", "cancelled"]).to_numpy()
    eligible = order_lines[eligible_mask].reset_index(drop=True)
    n = len(eligible)
    print(f"    allocating {n:,} eligible lines...")

    # Stores fulfill ~30% of allocations; DCs/dark stores the rest.
    sfs_pick = rng.random(n) < 0.30
    store_locs = locations[locations["location_type"] == "store"]["location_id"].to_numpy()
    other_locs = locations[locations["location_type"].isin(["dc", "dark_store", "drop_ship"])]["location_id"].to_numpy()
    loc_id = np.where(sfs_pick,
                      rng.choice(store_locs, size=n),
                      rng.choice(other_locs, size=n))

    rule_id = rng.choice(sourcing_rules["rule_id"].to_numpy(), size=n)

    allocated_at = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-08").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    ready_offset_min = rng.integers(15, 4 * 60, size=n)
    ready = allocated_at + pd.to_timedelta(ready_offset_min, unit="m")
    delivery_offset_h = rng.integers(24, 96, size=n)
    delivery = allocated_at + pd.to_timedelta(delivery_offset_h, unit="h")

    return pd.DataFrame({
        "allocation_id":         [f"ALC{i:010d}" for i in range(1, n + 1)],
        "order_line_id":         eligible["order_line_id"].to_numpy(),
        "location_id":           loc_id,
        "rule_id":               rule_id,
        "allocated_quantity":    eligible["quantity"].to_numpy(),
        "estimated_cost_minor":  (rng.lognormal(2.5, 0.7, size=n) * 100).astype(np.int64),
        "estimated_ready_ts":    ready,
        "estimated_delivery_ts": delivery,
        "status":                weighted_choice(rng, ["issued", "accepted", "rejected", "reallocated", "completed"],
                                                 [0.02, 0.06, 0.02, 0.04, 0.86], n),
        "allocated_at":          allocated_at,
    })


def _fulfillment_events(ctx, allocations, n=200_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(allocations), size=n)
    sub = allocations.iloc[a_idx].reset_index(drop=True)
    occurred_offset_min = rng.integers(0, 6 * 60, size=n)
    occurred = sub["allocated_at"].to_numpy() + pd.to_timedelta(occurred_offset_min, unit="m")
    return pd.DataFrame({
        "event_id":       [f"EVT{i:011d}" for i in range(1, n + 1)],
        "allocation_id":  sub["allocation_id"].to_numpy(),
        "order_line_id":  sub["order_line_id"].to_numpy(),
        "location_id":    sub["location_id"].to_numpy(),
        "event_type":     weighted_choice(rng, EVENT_TYPES, EVENT_TYPE_W, n),
        "occurred_at":    occurred,
        "actor_role":     weighted_choice(rng, ACTOR_ROLES, ACTOR_ROLE_W, n),
        "actor_id":       [f"ACT{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "payload_json":   ['{"src":"oms"}'] * n,
    })


def _shipments(ctx, allocations, locations, n=30_000):
    rng = ctx.rng
    n = min(n, len(allocations))
    sub = allocations.sample(n=n, random_state=ctx.seed + 7).reset_index(drop=True)
    shipped_offset_h = rng.integers(0, 48, size=n)
    shipped = sub["allocated_at"].to_numpy() + pd.to_timedelta(shipped_offset_h, unit="h")
    transit_h = rng.integers(8, 96, size=n)
    delivered = shipped + pd.to_timedelta(transit_h, unit="h")
    weight = rng.integers(120, 9000, size=n)

    return pd.DataFrame({
        "shipment_id":           [f"SHP{i:010d}" for i in range(1, n + 1)],
        "allocation_id":         sub["allocation_id"].to_numpy(),
        "tracking_number":       [f"TRK{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "carrier":               weighted_choice(rng, CARRIERS, CARRIER_W, n),
        "service_level":         weighted_choice(rng, SERVICE_LEVELS, SERVICE_LEVEL_W, n),
        "ship_from_location_id": sub["location_id"].to_numpy(),
        "ship_to_postal":        [f"{rng.integers(1000, 99999):05d}" for _ in range(n)],
        "ship_to_country_iso2":  rng.choice(COUNTRIES, size=n),
        "weight_grams":          weight,
        "cost_minor":            ((weight / 100.0) * rng.uniform(15, 80, size=n)).astype(np.int64),
        "shipped_at":            shipped,
        "delivered_at":          delivered,
        "status":                weighted_choice(rng, SHIPMENT_STATUSES, SHIPMENT_STATUS_W, n),
    })


def _returns(ctx, orders, customers, locations, n=10_000):
    rng = ctx.rng
    eligible = orders[orders["order_status"].isin(["delivered", "picked_up", "shipped", "returned"])].reset_index(drop=True)
    if len(eligible) < n:
        n = len(eligible)
    sub = eligible.sample(n=n, random_state=ctx.seed + 11).reset_index(drop=True)
    initiated = sub["closed_at"].fillna(sub["captured_at"]).to_numpy() + pd.to_timedelta(rng.integers(0, 30 * 24, size=n), unit="h")
    received_offset_h = rng.integers(24, 14 * 24, size=n)
    received = initiated + pd.to_timedelta(received_offset_h, unit="h")
    refund_offset_h = rng.integers(1, 7 * 24, size=n)
    refund_issued = received + pd.to_timedelta(refund_offset_h, unit="h")
    refund_amt = (sub["order_total_minor"].to_numpy() * rng.uniform(0.2, 1.0, size=n)).astype(np.int64)
    return_loc_pool = locations[locations["location_type"].isin(["store", "dc", "locker"])]["location_id"].to_numpy()

    return pd.DataFrame({
        "rma_id":               [f"RMA{i:010d}" for i in range(1, n + 1)],
        "order_id":             sub["order_id"].to_numpy(),
        "customer_id":          sub["customer_id"].to_numpy(),
        "return_reason":        weighted_choice(rng, RETURN_REASONS, RETURN_REASON_W, n),
        "return_method":        weighted_choice(rng, RETURN_METHODS, RETURN_METHOD_W, n),
        "return_location_id":   rng.choice(return_loc_pool, size=n),
        "refund_method":        weighted_choice(rng, REFUND_METHODS, REFUND_METHOD_W, n),
        "refund_amount_minor":  refund_amt,
        "restock_outcome":      weighted_choice(rng, RESTOCK_OUTCOMES, RESTOCK_OUTCOME_W, n),
        "initiated_at":         initiated,
        "received_at":          received,
        "refund_issued_at":     refund_issued,
        "status":               weighted_choice(rng, ["initiated", "in_transit", "received", "inspected", "refunded", "cancelled"],
                                                [0.04, 0.08, 0.05, 0.03, 0.78, 0.02], n),
    })


# -----------------------------------------------------------------------------
def generate(seed=42):
    ctx = make_context(seed)
    print("  generating customers...")
    customers = _customers(ctx)
    print("  generating locations...")
    locations = _locations(ctx)
    print("  generating products...")
    products = _products(ctx)
    print("  generating inventory_positions...")
    inventory = _inventory_positions(ctx, locations, products)
    print("  generating sourcing_rules...")
    rules = _sourcing_rules(ctx)
    print("  generating orders (100k)...")
    orders = _orders(ctx, customers, locations)
    print("  generating order_lines (~300k)...")
    order_lines = _order_lines(ctx, orders, products, locations)
    print("  generating allocations...")
    allocations = _allocations(ctx, order_lines, locations, rules)
    print("  generating fulfillment_events (200k)...")
    events = _fulfillment_events(ctx, allocations)
    print("  generating shipments...")
    shipments = _shipments(ctx, allocations, locations)
    print("  generating return_authorizations...")
    rmas = _returns(ctx, orders, customers, locations)

    # Drop the helper col before write.
    orders_to_write = orders.drop(columns=["_line_count"])

    tables = {
        "customer":              customers,
        "location":              locations,
        "product":               products,
        "inventory_position":    inventory,
        "sourcing_rule":         rules,
        "oms_order":             orders_to_write,
        "order_line":            order_lines,
        "allocation":            allocations,
        "fulfillment_event":     events,
        "shipment":              shipments,
        "return_authorization":  rmas,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
