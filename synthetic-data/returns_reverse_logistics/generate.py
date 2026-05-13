"""
Synthetic Returns & Reverse Logistics data — RMA + return_item + refund +
refurb + liquidation + fraud_signal + carrier_label tables modeled on the
Optoro / Loop / Narvar / Happy Returns / SAP S/4 Returns / Manhattan Active
WMS / Salesforce OMS / ZigZag / ReBound / Doddle / Newmine contract.

Scale targets (single year, single retailer):
  customers     : 200,000
  sales_orders  : 500,000           (8% return rate → ~40k RMAs)
  rmas          : 40,000
  return_items  : 60,000            (~1.5 items per RMA)
  refunds       : 42,000            (some RMAs split-refund; some returnless)
  refurb_outcomes: 30,000
  liquidation_lots: 5,000
  liquidation_lot_items: 50,000     (~10 items per lot avg)
  reason_codes  : 200                (master catalog)
  dispositions  : 8                  (master catalog)
  fraud_signals : 2,000
  carrier_labels: 36,000             (most RMAs ship; returnless skip)

All large IDs use the int64-safe pattern (rng.integers + zero-padded format
string) consistent with the loss_prevention / agentic_commerce generators.
PII columns are pre-hashed at generation time.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table  # noqa: E402

SUBDOMAIN = "returns_reverse_logistics"
TENANT_SALT = "rrl-tenant-salt-2026"

COUNTRIES = ["US", "GB", "DE", "FR", "CA", "AU", "NL", "ES", "IT", "JP", "MX", "BR"]
COUNTRY_W = [0.55, 0.10, 0.07, 0.05, 0.06, 0.04, 0.04, 0.03, 0.02, 0.02, 0.01, 0.01]

LOYALTY_TIERS = ["none", "bronze", "silver", "gold", "platinum"]
LOYALTY_W = [0.40, 0.30, 0.18, 0.09, 0.03]

CUSTOMER_STATUS = ["active", "restricted", "blocked"]
CUSTOMER_STATUS_W = [0.95, 0.04, 0.01]

CHANNELS = ["ecom", "store", "marketplace", "wholesale"]
CHANNEL_W = [0.62, 0.30, 0.07, 0.01]

CATEGORIES = ["apparel", "footwear", "electronics", "home", "beauty", "outdoor", "toys", "books", "kitchen", "appliances"]
CATEGORY_W = [0.34, 0.16, 0.14, 0.10, 0.08, 0.06, 0.05, 0.03, 0.02, 0.02]

RETURN_METHODS = ["mail", "boris_store", "happy_returns_bar", "doddle_qr", "carrier_pickup", "locker", "returnless"]
RETURN_METHOD_W = [0.46, 0.21, 0.14, 0.06, 0.04, 0.02, 0.07]

RETURN_PLATFORMS = ["Loop", "Narvar", "Optoro", "HappyReturns", "ReBound", "ZigZag", "Doddle", "in_house",
                    "Salesforce_OMS", "SAP_S4_Returns", "Manh_Active_WMS"]
RETURN_PLATFORM_W = [0.20, 0.16, 0.14, 0.12, 0.06, 0.05, 0.05, 0.08, 0.05, 0.05, 0.04]

CARRIERS = ["USPS", "UPS", "FedEx", "Hermes", "EVRi", "YunExpress", "HappyReturns", "n/a"]
CARRIER_W = [0.22, 0.28, 0.20, 0.04, 0.03, 0.03, 0.12, 0.08]

RMA_STATUS = ["issued", "in_transit", "received", "cancelled", "expired"]
RMA_STATUS_W = [0.06, 0.10, 0.74, 0.06, 0.04]

# Reason category distribution
REASON_CATEGORIES = ["fit", "quality", "wrong_item", "damaged", "changed_mind", "late", "gift", "wardrobing", "fraud_suspected", "other"]
REASON_CATEGORY_W = [0.30, 0.16, 0.10, 0.10, 0.18, 0.04, 0.04, 0.04, 0.02, 0.02]

DEFECT_ATTRIBUTION = ["supplier", "carrier", "merchant", "customer", "unknown"]
DEFECT_W = [0.18, 0.10, 0.08, 0.50, 0.14]

SEVERITY = ["low", "medium", "high", "critical"]
SEVERITY_W = [0.42, 0.40, 0.15, 0.03]

CONDITION_GRADES = ["A", "B", "C", "D", "scrap"]
CONDITION_W = [0.42, 0.28, 0.16, 0.10, 0.04]

DISPOSITION_CODES = ["restock_A", "restock_open_box", "refurb", "b_stock_liquidation", "donation", "recycle", "scrap", "returnless"]
DISPOSITION_W = [0.40, 0.12, 0.16, 0.14, 0.04, 0.04, 0.03, 0.07]

REFUND_TYPES = ["original_tender", "store_credit", "exchange", "gift_card", "returnless"]
REFUND_TYPE_W = [0.66, 0.12, 0.08, 0.07, 0.07]

PAYMENT_RAILS = ["card", "paypal", "ach", "store_credit", "gift_card", "crypto"]
PAYMENT_RAIL_W = [0.66, 0.14, 0.04, 0.08, 0.07, 0.01]

REFUND_STATUS = ["pending", "issued", "failed", "reversed"]
REFUND_STATUS_W = [0.04, 0.93, 0.02, 0.01]

REFURB_OUTCOMES = ["refurbed_A", "refurbed_B", "refurbed_open_box", "scrapped", "sent_to_liquidation", "returned_to_vendor"]
REFURB_OUTCOME_W = [0.34, 0.26, 0.18, 0.08, 0.10, 0.04]

POST_REFURB_GRADES = ["A", "B", "C", "scrap"]
POST_REFURB_W = [0.34, 0.36, 0.22, 0.08]

LIQ_MARKETPLACES = ["B-Stock", "Liquidation_com", "BULQ", "Direct_Liquidation", "eBay_B-Stock", "Optoro_OptiTurn"]
LIQ_MARKETPLACE_W = [0.36, 0.18, 0.18, 0.10, 0.08, 0.10]

FRAUD_SOURCES = ["Newmine", "Appriss_Retail", "internal_xgb", "Loop_workflow", "Narvar_rule", "Optoro_flag"]
FRAUD_SOURCE_W = [0.30, 0.22, 0.20, 0.10, 0.10, 0.08]

FRAUD_SIGNAL_TYPES = ["wardrobing", "serial_returner", "wrong_item_swap", "empty_box", "receipt_fraud",
                     "cross_border_abuse", "return_to_different_store", "chronic_returner"]
FRAUD_SIGNAL_W = [0.22, 0.18, 0.12, 0.06, 0.10, 0.06, 0.10, 0.16]

FRAUD_RECOMMENDATIONS = ["approve", "verify", "deny", "stepup_required"]
FRAUD_RECO_W = [0.46, 0.30, 0.16, 0.08]

SERVICE_LEVELS = ["ground", "expedited", "consolidation", "drop_off_qr", "return_bar"]
SERVICE_LEVEL_W = [0.50, 0.10, 0.16, 0.08, 0.16]

LABEL_STATUS = ["issued", "in_transit", "delivered", "exception", "void"]
LABEL_STATUS_W = [0.06, 0.10, 0.76, 0.05, 0.03]

CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "BRL", "MXN"]
CURRENCY_W = [0.60, 0.14, 0.10, 0.06, 0.04, 0.03, 0.02, 0.01]

REFUND_OUTCOMES_BY_TYPE = {
    "returnless": "returnless",
    # rest are pass-through
}


def _hash(value: str) -> str:
    return hashlib.sha256(f"{value}{TENANT_SALT}".encode()).hexdigest()


# ---------------------------------------------------------------------------
def _customers(ctx, n=200_000):
    rng = ctx.rng
    loyalty = weighted_choice(rng, LOYALTY_TIERS, LOYALTY_W, n)
    ltv_orders = rng.integers(1, 80, size=n)
    ltv_returns = (ltv_orders * rng.uniform(0.0, 0.4, size=n)).astype(int)
    chronic_score = np.where(
        ltv_returns / np.maximum(ltv_orders, 1) > 0.30,
        np.clip(rng.normal(0.70, 0.15, size=n), 0, 1),
        np.clip(rng.beta(2, 25, size=n), 0, 1),
    )
    chronic_flag = chronic_score > 0.55
    cust_ids = [f"CST{i:08d}" for i in range(1, n + 1)]
    return pd.DataFrame({
        "customer_id": cust_ids,
        "customer_ref_hash": [_hash(c) for c in cust_ids],
        "country_iso2": weighted_choice(rng, COUNTRIES, COUNTRY_W, n),
        "loyalty_tier": loyalty,
        "lifetime_orders": ltv_orders.astype(np.int64),
        "lifetime_returns": ltv_returns.astype(np.int64),
        "chronic_returner_flag": chronic_flag,
        "chronic_returner_score": np.round(chronic_score, 3),
        "status": np.where(chronic_flag & (rng.random(n) < 0.10),
                           weighted_choice(rng, ["restricted", "blocked"], [0.85, 0.15], n),
                           "active"),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2022-01-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
    })


def _sales_orders(ctx, customers, n=500_000):
    rng = ctx.rng
    c_idx = rng.integers(0, len(customers), size=n)
    subtotal = (rng.lognormal(4.4, 0.9, size=n) * 100).astype(np.int64)
    tax = (subtotal * rng.uniform(0.0, 0.20, size=n)).astype(np.int64)
    shipping = rng.choice([0, 499, 799, 1299], size=n).astype(np.int64)
    total = subtotal + tax + shipping
    return pd.DataFrame({
        "order_id": [f"ORD{i:09d}" for i in range(1, n + 1)],
        "customer_id": customers["customer_id"].to_numpy()[c_idx],
        "channel": weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "order_ts": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2025-04-01").timestamp()),
                         int(pd.Timestamp("2026-04-30").timestamp()), size=n),
            unit="s"),
        "ship_node": rng.choice([f"DC{i:03d}" for i in range(1, 41)] +
                                [f"STR{i:04d}" for i in range(1, 201)], size=n),
        "subtotal_minor": subtotal,
        "shipping_minor": shipping,
        "tax_minor": tax,
        "total_minor": total,
        "currency": weighted_choice(rng, CURRENCIES, CURRENCY_W, n),
    })


def _reason_codes(ctx, n=200):
    rng = ctx.rng
    cats = weighted_choice(rng, REASON_CATEGORIES, REASON_CATEGORY_W, n)
    code_text = {
        "fit": ["TOO_SMALL", "TOO_LARGE", "FIT_WRONG_LENGTH", "FIT_WRONG_WIDTH", "FIT_CUT_OFF", "TOO_TIGHT", "TOO_LOOSE"],
        "quality": ["QUALITY_DEFECT", "STITCHING_LOOSE", "MATERIAL_THIN", "COLOR_FADED", "SMELL_OFF", "ZIPPER_BROKEN"],
        "wrong_item": ["WRONG_ITEM_SHIPPED", "WRONG_COLOR", "WRONG_SIZE_SHIPPED", "WRONG_STYLE"],
        "damaged": ["DAMAGED_IN_TRANSIT", "DAMAGED_BOX", "ITEM_BROKEN", "WATER_DAMAGE"],
        "changed_mind": ["CHANGED_MIND", "FOUND_CHEAPER", "NO_LONGER_NEEDED", "BOUGHT_TWICE"],
        "late": ["DELIVERED_LATE", "PAST_EVENT_DATE", "MISSED_GIFT_OCCASION"],
        "gift": ["GIFT_RECIPIENT_REJECTED", "GIFT_DUPLICATE", "GIFT_RETURN"],
        "wardrobing": ["WARDROBING_SUSPECTED", "WORN_AND_RETURNED"],
        "fraud_suspected": ["EMPTY_BOX", "ITEM_SWAP_SUSPECTED", "RECEIPT_INCONSISTENT"],
        "other": ["OTHER", "UNSPECIFIED", "CUSTOMER_NOTE_PROVIDED"],
    }
    code_text_arr = np.array([rng.choice(code_text[c]) + f"_{i:03d}" for i, c in enumerate(cats)])
    return pd.DataFrame({
        "reason_code_id": [f"RC{i:04d}" for i in range(1, n + 1)],
        "reason_code": code_text_arr,
        "reason_category": cats,
        "customer_facing_text": [f"Reason {i}" for i in range(1, n + 1)],
        "defect_attribution": weighted_choice(rng, DEFECT_ATTRIBUTION, DEFECT_W, n),
        "actionable": rng.random(n) < 0.68,
        "severity": weighted_choice(rng, SEVERITY, SEVERITY_W, n),
    })


def _dispositions(ctx):
    rng = ctx.rng
    rows = [
        ("DIS001", "restock_A",            "Restock to Primary Inventory",   "primary_inventory",   0.95, "in_house_CRC"),
        ("DIS002", "restock_open_box",     "Restock as Open-Box",            "open_box",            0.65, "in_house_CRC"),
        ("DIS003", "refurb",               "Route to Refurbishment",         "primary_inventory",   0.55, "Optoro"),
        ("DIS004", "b_stock_liquidation",  "Liquidate via B-Stock",          "b_stock_marketplace", 0.20, "Optoro"),
        ("DIS005", "donation",             "Donate via Good360 / Goodwill",  "donation_partner",    0.10, "Good360"),
        ("DIS006", "recycle",              "Recycle (Materials Recovery)",   "recycler",            0.05, "local_recycler"),
        ("DIS007", "scrap",                "Scrap / Landfill",               "landfill",            0.00, "in_house_CRC"),
        ("DIS008", "returnless",           "Returnless Refund (Keep It)",    "n/a",                 0.00, "Loop"),
    ]
    return pd.DataFrame(rows, columns=[
        "disposition_id", "disposition_code", "disposition_name", "target_channel",
        "typical_recovery_pct", "lane_owner",
    ])


def _rmas(ctx, orders, customers, n=40_000):
    rng = ctx.rng
    if n > len(orders):
        n = len(orders)
    sub_orders = orders.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    issued = sub_orders["order_ts"].to_numpy() + pd.to_timedelta(rng.integers(86400, 30 * 86400, size=n), unit="s")
    expires = issued + pd.to_timedelta(rng.integers(7, 60, size=n), unit="D")
    return_method = weighted_choice(rng, RETURN_METHODS, RETURN_METHOD_W, n)
    cross_border = rng.random(n) < 0.08
    source_country = sub_orders.merge(customers[["customer_id", "country_iso2"]], on="customer_id", how="left")["country_iso2"].to_numpy()
    dest_country = np.where(cross_border, "US", source_country)
    restocking_eligible = (sub_orders["subtotal_minor"].to_numpy() * rng.uniform(0.0, 0.20, size=n)).astype(np.int64)
    return pd.DataFrame({
        "rma_id": [f"RMA{i:09d}" for i in range(1, n + 1)],
        "order_id": sub_orders["order_id"].to_numpy(),
        "customer_id": sub_orders["customer_id"].to_numpy(),
        "issued_ts": issued,
        "expires_ts": expires,
        "return_method": return_method,
        "return_platform": weighted_choice(rng, RETURN_PLATFORMS, RETURN_PLATFORM_W, n),
        "carrier": np.where(return_method == "returnless", "n/a", weighted_choice(rng, CARRIERS, CARRIER_W, n)),
        "tracking_number": [f"1Z{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "cross_border": cross_border,
        "source_country_iso2": source_country,
        "destination_country_iso2": dest_country,
        "rma_status": weighted_choice(rng, RMA_STATUS, RMA_STATUS_W, n),
        "restocking_fee_eligible_minor": restocking_eligible,
        "epcis_event_uri": [f"epcis://retailer.example/event/{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
    })


def _return_items(ctx, rmas, reason_codes, dispositions, n=60_000):
    rng = ctx.rng
    # 1-4 items per RMA (avg ~1.5)
    rma_idx = rng.integers(0, len(rmas), size=n)
    sub = rmas.iloc[rma_idx].reset_index(drop=True)
    unit_cogs = (rng.lognormal(3.4, 0.8, size=n) * 100).astype(np.int64)
    unit_retail = (unit_cogs * rng.uniform(1.5, 3.5, size=n)).astype(np.int64)
    # disposition decided 0-21 days after RMA issue
    disposition_decided = sub["issued_ts"].to_numpy() + pd.to_timedelta(rng.integers(0, 21, size=n), unit="D")
    # Returnless RMAs always get the returnless disposition; receive items follow grade distribution
    grade = weighted_choice(rng, CONDITION_GRADES, CONDITION_W, n)
    disp = weighted_choice(rng, DISPOSITION_CODES, DISPOSITION_W, n)
    disp = np.where(sub["return_method"].to_numpy() == "returnless", "returnless", disp)
    disp_id = pd.Series(disp).map(dict(zip(dispositions["disposition_code"], dispositions["disposition_id"]))).to_numpy()
    reason_id = reason_codes["reason_code_id"].to_numpy()[rng.integers(0, len(reason_codes), size=n)]
    return pd.DataFrame({
        "return_item_id": [f"RI{i:010d}" for i in range(1, n + 1)],
        "rma_id": sub["rma_id"].to_numpy(),
        "order_id": sub["order_id"].to_numpy(),
        "sku_id": [f"SKU{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "gtin": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "category": weighted_choice(rng, CATEGORIES, CATEGORY_W, n),
        "quantity": rng.integers(1, 5, size=n).astype(np.int32),
        "unit_cogs_minor": unit_cogs,
        "unit_retail_minor": unit_retail,
        "reason_code_id": reason_id,
        "condition_grade": grade,
        "disposition_id": disp_id,
        "disposition_decided_ts": disposition_decided,
        "serial_number": np.where(rng.random(n) < 0.30,
                                  [f"SN{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
                                  None),
    })


def _refunds(ctx, rmas, orders, customers, n=42_000):
    rng = ctx.rng
    if n > len(rmas):
        n = len(rmas)
    sub = rmas.sample(n=n, random_state=ctx.seed + 1).reset_index(drop=True)
    sub_orders = sub.merge(orders[["order_id", "subtotal_minor", "currency"]], on="order_id", how="left")
    refund_type = np.where(sub["return_method"].to_numpy() == "returnless",
                           "returnless",
                           weighted_choice(rng, REFUND_TYPES, REFUND_TYPE_W, n))
    base_amount = sub_orders["subtotal_minor"].to_numpy() * rng.uniform(0.30, 1.0, size=n)
    restocking_collected = np.where(rng.random(n) < 0.20,
                                    (sub["restocking_fee_eligible_minor"].to_numpy() * 0.85).astype(np.int64),
                                    0).astype(np.int64)
    refund_amount = (base_amount - restocking_collected).astype(np.int64).clip(min=100)
    issued = sub["issued_ts"].to_numpy() + pd.to_timedelta(rng.integers(3, 168, size=n), unit="h")
    return pd.DataFrame({
        "refund_id": [f"REF{i:010d}" for i in range(1, n + 1)],
        "rma_id": sub["rma_id"].to_numpy(),
        "order_id": sub["order_id"].to_numpy(),
        "customer_id": sub["customer_id"].to_numpy(),
        "refund_type": refund_type,
        "refund_amount_minor": refund_amount,
        "currency": sub_orders["currency"].to_numpy(),
        "restocking_fee_collected_minor": restocking_collected,
        "issued_ts": issued,
        "psp_refund_id": [f"re_{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "payment_rail": weighted_choice(rng, PAYMENT_RAILS, PAYMENT_RAIL_W, n),
        "status": weighted_choice(rng, REFUND_STATUS, REFUND_STATUS_W, n),
    })


def _refurb_outcomes(ctx, return_items, n=30_000):
    rng = ctx.rng
    # Only return_items dispatched to refurb / restock_open_box are candidates
    candidates = return_items[return_items["disposition_id"].isin(["DIS002", "DIS003"])].reset_index(drop=True)
    if len(candidates) < n:
        n = len(candidates)
    sub = candidates.sample(n=n, random_state=ctx.seed + 2).reset_index(drop=True)
    started = sub["disposition_decided_ts"].to_numpy() + pd.to_timedelta(rng.integers(3600, 5 * 86400, size=n), unit="s")
    labor = rng.integers(5, 240, size=n)
    completed = started + pd.to_timedelta(rng.integers(86400, 14 * 86400, size=n), unit="s")
    parts_cost = (rng.lognormal(2.0, 1.2, size=n) * 100).astype(np.int64)
    outcome = weighted_choice(rng, REFURB_OUTCOMES, REFURB_OUTCOME_W, n)
    post_grade = weighted_choice(rng, POST_REFURB_GRADES, POST_REFURB_W, n)
    resale = (sub["unit_retail_minor"].to_numpy() *
              np.where(post_grade == "A", rng.uniform(0.75, 0.95, size=n),
              np.where(post_grade == "B", rng.uniform(0.50, 0.70, size=n),
              np.where(post_grade == "C", rng.uniform(0.20, 0.45, size=n),
                       rng.uniform(0.00, 0.05, size=n))))).astype(np.int64)
    return pd.DataFrame({
        "refurb_outcome_id": [f"REF_OUT{i:09d}" for i in range(1, n + 1)],
        "return_item_id": sub["return_item_id"].to_numpy(),
        "crc_id": rng.choice([f"CRC{i:02d}" for i in range(1, 13)], size=n),
        "started_ts": started,
        "completed_ts": completed,
        "labor_minutes": labor.astype(np.int32),
        "parts_cost_minor": parts_cost,
        "outcome": outcome,
        "post_refurb_grade": post_grade,
        "post_refurb_resale_value_minor": resale,
    })


def _liquidation_lots(ctx, n=5_000):
    rng = ctx.rng
    item_count = rng.integers(20, 250, size=n)
    cogs = (item_count * rng.lognormal(3.5, 0.7, size=n) * 100).astype(np.int64)
    recovery = rng.beta(2, 6, size=n)
    proceeds = (cogs * recovery).astype(np.int64)
    starting_bid = (proceeds * rng.uniform(0.30, 0.80, size=n)).astype(np.int64)
    winning_bid = proceeds
    listed = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                     int(pd.Timestamp("2026-04-30").timestamp()), size=n),
        unit="s")
    sold = listed + pd.to_timedelta(rng.integers(2, 30, size=n), unit="D")
    return pd.DataFrame({
        "lot_id": [f"LOT{i:08d}" for i in range(1, n + 1)],
        "marketplace": weighted_choice(rng, LIQ_MARKETPLACES, LIQ_MARKETPLACE_W, n),
        "lot_name": [f"Mixed Lot {i:04d}" for i in range(1, n + 1)],
        "item_count": item_count.astype(np.int64),
        "total_cogs_minor": cogs,
        "starting_bid_minor": starting_bid,
        "winning_bid_minor": winning_bid,
        "proceeds_minor": proceeds,
        "currency": rng.choice(["USD", "EUR", "GBP"], p=[0.78, 0.14, 0.08], size=n),
        "listed_ts": listed,
        "sold_ts": sold,
        "buyer_country_iso2": weighted_choice(rng, COUNTRIES, COUNTRY_W, n),
        "recovery_pct": np.round(recovery, 4),
    })


def _liquidation_lot_items(ctx, lots, return_items):
    rng = ctx.rng
    liquidated_items = return_items[return_items["disposition_id"] == "DIS004"].reset_index(drop=True)
    if len(liquidated_items) == 0:
        return pd.DataFrame(columns=[
            "lot_item_id", "lot_id", "return_item_id", "allocated_cogs_minor", "allocated_proceeds_minor",
        ])
    n = len(liquidated_items)
    lot_idx = rng.integers(0, len(lots), size=n)
    sub_lots = lots.iloc[lot_idx].reset_index(drop=True)
    # Pro-rate by unit_cogs
    allocated_cogs = liquidated_items["unit_cogs_minor"].to_numpy().astype(np.int64)
    allocated_proceeds = (allocated_cogs * sub_lots["recovery_pct"].to_numpy()).astype(np.int64)
    return pd.DataFrame({
        "lot_item_id": [f"LI{i:010d}" for i in range(1, n + 1)],
        "lot_id": sub_lots["lot_id"].to_numpy(),
        "return_item_id": liquidated_items["return_item_id"].to_numpy(),
        "allocated_cogs_minor": allocated_cogs,
        "allocated_proceeds_minor": allocated_proceeds,
    })


def _fraud_signals(ctx, rmas, customers, n=2_000):
    rng = ctx.rng
    if n > len(rmas):
        n = len(rmas)
    sub = rmas.sample(n=n, random_state=ctx.seed + 3).reset_index(drop=True)
    return pd.DataFrame({
        "fraud_signal_id": [f"FS{i:09d}" for i in range(1, n + 1)],
        "rma_id": sub["rma_id"].to_numpy(),
        "customer_id": sub["customer_id"].to_numpy(),
        "source": weighted_choice(rng, FRAUD_SOURCES, FRAUD_SOURCE_W, n),
        "signal_type": weighted_choice(rng, FRAUD_SIGNAL_TYPES, FRAUD_SIGNAL_W, n),
        "score": np.round(rng.beta(5, 3, size=n), 3),
        "recommendation": weighted_choice(rng, FRAUD_RECOMMENDATIONS, FRAUD_RECO_W, n),
        "scored_at": sub["issued_ts"].to_numpy() + pd.to_timedelta(rng.integers(60, 3600, size=n), unit="s"),
    })


def _carrier_labels(ctx, rmas):
    rng = ctx.rng
    shipped = rmas[rmas["return_method"] != "returnless"].reset_index(drop=True)
    n = len(shipped)
    label_cost = rng.choice([0, 299, 499, 799, 1299, 1999], p=[0.30, 0.18, 0.22, 0.16, 0.10, 0.04], size=n).astype(np.int64)
    service = weighted_choice(rng, SERVICE_LEVELS, SERVICE_LEVEL_W, n)
    co2e = np.where(np.isin(service, ["consolidation", "return_bar"]),
                    rng.uniform(0.4, 1.2, size=n),
                    rng.uniform(0.8, 3.6, size=n))
    created = shipped["issued_ts"].to_numpy() + pd.to_timedelta(rng.integers(60, 3600, size=n), unit="s")
    scanned = created + pd.to_timedelta(rng.integers(3600, 4 * 86400, size=n), unit="s")
    delivered = scanned + pd.to_timedelta(rng.integers(86400, 9 * 86400, size=n), unit="s")
    return pd.DataFrame({
        "label_id": [f"LBL{i:010d}" for i in range(1, n + 1)],
        "rma_id": shipped["rma_id"].to_numpy(),
        "carrier": shipped["carrier"].to_numpy(),
        "service_level": service,
        "label_cost_minor": label_cost,
        "prepaid_by_merchant": rng.random(n) < 0.78,
        "created_ts": created,
        "scanned_ts": scanned,
        "delivered_ts": delivered,
        "status": weighted_choice(rng, LABEL_STATUS, LABEL_STATUS_W, n),
        "scope3_kg_co2e": np.round(co2e, 3),
    })


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating customers...")
    customers = _customers(ctx)
    print("  generating sales_orders...")
    orders = _sales_orders(ctx, customers)
    print("  generating reason_codes...")
    reason_codes = _reason_codes(ctx)
    print("  generating dispositions...")
    dispositions = _dispositions(ctx)
    print("  generating return_authorizations...")
    rmas = _rmas(ctx, orders, customers)
    print("  generating return_items...")
    return_items = _return_items(ctx, rmas, reason_codes, dispositions)
    print("  generating refunds...")
    refunds = _refunds(ctx, rmas, orders, customers)
    print("  generating refurb_outcomes...")
    refurb_outcomes = _refurb_outcomes(ctx, return_items)
    print("  generating liquidation_lots...")
    lots = _liquidation_lots(ctx)
    print("  generating liquidation_lot_items...")
    lot_items = _liquidation_lot_items(ctx, lots, return_items)
    print("  generating fraud_signals...")
    fraud = _fraud_signals(ctx, rmas, customers)
    print("  generating carrier_labels...")
    labels = _carrier_labels(ctx, rmas)
    tables = {
        "customer": customers,
        "sales_order": orders,
        "reason_code": reason_codes,
        "disposition": dispositions,
        "return_authorization": rmas,
        "return_item": return_items,
        "refund": refunds,
        "refurb_outcome": refurb_outcomes,
        "liquidation_lot": lots,
        "liquidation_lot_item": lot_items,
        "fraud_signal": fraud,
        "carrier_label": labels,
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
