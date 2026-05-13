"""
Synthetic Trade Promotion Management data — SAP TPM / Exceedra / BluePlanner /
Anaplan TPM / IRI/Circana / NielsenIQ / Numerator / retailer EDI 852/867.

Entities (>=10):
  account, customer_outlet, product, promotion, promo_tactic, deduction,
  baseline_forecast, lift_observation, retailer_scan_data, trade_fund.

Realism:
  - 5k accounts (HQ-level retailers + banner roll-ups, long-tail Pareto on spend)
  - 500 SKUs with brand / pack / category hierarchy (lognormal ABC volume)
  - 8 fiscal quarters (FY2025-Q1 through FY2026-Q4) of plan + actual data
  - ~5 promotions per account per quarter → ~200k promo plans
  - ~4 tactics per promotion → ~800k tactics
  - ~50k deductions, with claim-to-tactic match probability 0.62
  - ~2M retailer scan-data rows (stratified across EDI 852, Circana, Numerator)
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
from common import (
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "trade_promotion_management"

# ---------------------------------------------------------------------------
# Reference distributions

CHANNELS = ["grocery", "mass", "club", "drug", "convenience", "dollar", "ecom", "food_service"]
CHANNEL_W = [0.34, 0.18, 0.07, 0.10, 0.13, 0.08, 0.07, 0.03]

ACCOUNT_STATUS = ["active", "active", "active", "inactive", "review"]

TRADE_TERMS = ["off_invoice_only", "scan_down_only", "mixed", "edlp_focus", "pay_for_performance"]
TRADE_TERMS_W = [0.18, 0.08, 0.55, 0.12, 0.07]

OUTLET_FORMATS = ["supercenter", "grocery", "club", "express", "c-store", "drug"]
OUTLET_FORMAT_W = [0.10, 0.45, 0.04, 0.06, 0.30, 0.05]

US_STATES = [
    "CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI",
    "NJ", "VA", "WA", "AZ", "MA", "TN", "IN", "MO", "MD", "WI",
]

CATEGORIES = [
    ("Carbonated Beverages", "CSD"),
    ("Salty Snacks", "Chips"),
    ("Salty Snacks", "Pretzels"),
    ("Confectionery", "Chocolate"),
    ("Confectionery", "Gum"),
    ("Personal Care", "Shampoo"),
    ("Personal Care", "Deodorant"),
    ("Household", "Laundry"),
    ("Household", "Paper"),
    ("Frozen", "Pizza"),
    ("Frozen", "Ice Cream"),
    ("Dairy", "Yogurt"),
    ("Cereal", "RTE Cereal"),
    ("Coffee", "Single-Serve"),
]

BRANDS = [
    "Pepsi", "Coca-Cola", "Frito-Lay", "Hershey", "Mondelez",
    "Procter & Gamble", "Unilever", "Kellanova", "General Mills",
    "Nestle", "Mars Wrigley", "Colgate-Palmolive", "Conagra", "Kraft Heinz",
]

PACK_SIZES = ["12oz can 12pk", "20oz btl", "2L btl", "1.5oz bag", "9.75oz bag",
              "16oz bag", "8ct bar", "4-pack", "100ct box", "32oz tub"]

TACTIC_TYPES = ["off_invoice", "scan_down", "bill_back", "mcb", "edlp",
                "trade_allowance", "display", "feature", "tpr", "coupon", "bogo"]
TACTIC_W = [0.22, 0.16, 0.10, 0.08, 0.05, 0.07, 0.10, 0.10, 0.08, 0.02, 0.02]

FEATURE_TYPES = ["ad_block", "insert", "email", "in_app", "none"]
DISPLAY_TYPES = ["endcap", "aisle_violator", "pallet_drop", "cooler", "none"]
SETTLEMENT_METHODS = ["off_invoice", "deduction", "check", "emc", "edi820"]

PROMO_STATUS = ["draft", "approved", "active", "closed", "cancelled"]
PROMO_STATUS_W = [0.05, 0.10, 0.20, 0.60, 0.05]

DEDUCTION_TYPES = ["promo", "shortage", "damages", "pricing", "compliance",
                   "slotting", "mcb", "other"]
DEDUCTION_TYPE_W = [0.55, 0.10, 0.05, 0.08, 0.07, 0.05, 0.07, 0.03]

DEDUCTION_STATUS = ["open", "matched", "disputed", "paid", "written_off", "chargeback_lost"]
DEDUCTION_STATUS_W = [0.18, 0.22, 0.12, 0.38, 0.07, 0.03]

DISPUTE_REASONS = [
    "no_proof_of_promo", "tactic_mismatch", "duplicate_claim", "out_of_window",
    "pricing_error", "math_error", "compliance_unverified",
]

BASELINE_MODELS = [
    ("circana_unify", "v8.3"),
    ("niq_baseline", "2026.1"),
    ("tpro_predictive", "v4.2"),
    ("inhouse_glm", "2026.q1"),
]

LIFT_SOURCES = ["circana", "niq", "numerator", "inhouse", "retailer_scan"]
LIFT_SOURCES_W = [0.32, 0.28, 0.10, 0.18, 0.12]

SCAN_SOURCES = ["EDI 852", "EDI 867", "circana", "niq", "numerator", "first_party"]
SCAN_SOURCES_W = [0.42, 0.10, 0.20, 0.18, 0.05, 0.05]

FUND_TYPES = ["accrual", "lump_sum", "pay_for_performance", "mcb_pool"]
FUND_TYPES_W = [0.55, 0.20, 0.15, 0.10]

# ---------------------------------------------------------------------------
# Generators

def _accounts(ctx, n=5_000):
    rng = ctx.rng
    f = ctx.faker
    parent_pool = [f"ACC{i:06d}" for i in rng.integers(1, max(2, n // 50), size=n)]
    return pd.DataFrame({
        "account_id": [f"ACC{i:06d}" for i in range(1, n + 1)],
        "account_name": [f.company() for _ in range(n)],
        "parent_account_id": parent_pool,
        "channel": weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "country_iso2": rng.choice(["US", "CA", "MX", "GB", "DE", "FR", "ES", "IT"], size=n,
                                    p=[0.62, 0.10, 0.06, 0.06, 0.05, 0.05, 0.03, 0.03]),
        "gln": [f"{rng.integers(10**12, 10**13):013d}" for _ in range(n)],
        "trade_terms_code": weighted_choice(rng, TRADE_TERMS, TRADE_TERMS_W, n),
        "status": rng.choice(ACCOUNT_STATUS, size=n),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2018-01-01").timestamp()),
                         int(pd.Timestamp("2025-12-31").timestamp()), size=n),
            unit="s"),
    })


def _outlets(ctx, accounts, n=20_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    sub = accounts.iloc[a_idx].reset_index(drop=True)
    return pd.DataFrame({
        "outlet_id": [f"OUT{i:07d}" for i in range(1, n + 1)],
        "account_id": sub["account_id"].to_numpy(),
        "store_number": [f"{rng.integers(1, 9999):04d}" for _ in range(n)],
        "gln": [f"{rng.integers(10**12, 10**13):013d}" for _ in range(n)],
        "country_iso2": sub["country_iso2"].to_numpy(),
        "state_region": rng.choice(US_STATES, size=n),
        "postal_code": [f"{rng.integers(10**4, 10**5):05d}" for _ in range(n)],
        "format": weighted_choice(rng, OUTLET_FORMATS, OUTLET_FORMAT_W, n),
        "lat": np.round(rng.uniform(25.0, 49.0, size=n), 6),
        "lng": np.round(rng.uniform(-124.0, -67.0, size=n), 6),
        "opened_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("1990-01-01").timestamp()),
                         int(pd.Timestamp("2024-06-30").timestamp()), size=n),
            unit="s").date,
        "status": rng.choice(["active", "active", "active", "remodel", "closed"], size=n),
    })


def _products(ctx, n=500):
    rng = ctx.rng
    cat_idx = rng.integers(0, len(CATEGORIES), size=n)
    cats = [CATEGORIES[i] for i in cat_idx]
    list_price = (rng.lognormal(2.4, 0.6, size=n) * 100).astype(np.int64)  # cents
    return pd.DataFrame({
        "sku_id": [f"SKU{i:05d}" for i in range(1, n + 1)],
        "gtin": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "brand": rng.choice(BRANDS, size=n),
        "sub_brand": [f"Sub-{rng.integers(1, 50):02d}" for _ in range(n)],
        "category": [c[0] for c in cats],
        "subcategory": [c[1] for c in cats],
        "pack_size": rng.choice(PACK_SIZES, size=n),
        "case_pack_qty": rng.choice([6, 8, 12, 12, 12, 18, 24, 24, 36, 48], size=n).astype("int16"),
        "list_price_cents": list_price,
        "srp_cents": (list_price * rng.uniform(1.20, 1.65, size=n)).astype(np.int64),
        "cost_of_goods_cents": (list_price * rng.uniform(0.45, 0.70, size=n)).astype(np.int64),
        "launch_date": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2010-01-01").timestamp()),
                         int(pd.Timestamp("2025-12-31").timestamp()), size=n),
            unit="s").date,
        "status": rng.choice(["active", "active", "active", "discontinued", "phasing_in"], size=n),
    })


def _promotions(ctx, accounts, n=200_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    quarters = [
        ("2025-01-06", "2025-03-30", 2025, 1),
        ("2025-04-07", "2025-06-29", 2025, 2),
        ("2025-07-07", "2025-09-28", 2025, 3),
        ("2025-10-06", "2025-12-28", 2025, 4),
        ("2026-01-05", "2026-03-29", 2026, 1),
        ("2026-04-06", "2026-06-28", 2026, 2),
        ("2026-07-06", "2026-09-27", 2026, 3),
        ("2026-10-05", "2026-12-27", 2026, 4),
    ]
    q_idx = rng.integers(0, len(quarters), size=n)
    fy = np.array([quarters[i][2] for i in q_idx])
    fq = np.array([quarters[i][3] for i in q_idx])
    q_starts = np.array([pd.Timestamp(quarters[i][0]).value // 10**9 for i in q_idx])
    q_ends = np.array([pd.Timestamp(quarters[i][1]).value // 10**9 for i in q_idx])
    offset_within_quarter = rng.integers(0, np.maximum(1, q_ends - q_starts - 30 * 86400), size=n)
    start_ts = q_starts + offset_within_quarter
    duration_days = rng.integers(7, 28, size=n)
    end_ts = start_ts + duration_days.astype(np.int64) * 86400
    ship_offset = rng.integers(7 * 86400, 21 * 86400, size=n)
    ship_start_ts = start_ts - ship_offset
    ship_end_ts = end_ts + 7 * 86400
    planned_spend = (rng.lognormal(8.0, 1.2, size=n) * 100).astype(np.int64)
    planned_volume = (rng.lognormal(7.5, 1.0, size=n)).astype(np.int64)
    planned_lift = np.round(rng.normal(35, 18, size=n).clip(-10, 200), 2)
    forecast_roi = np.round(rng.normal(1.4, 0.8, size=n).clip(-0.5, 8.0), 2)
    status = weighted_choice(rng, PROMO_STATUS, PROMO_STATUS_W, n)
    created_at = pd.to_datetime(start_ts - rng.integers(30 * 86400, 90 * 86400, size=n), unit="s")
    approved_mask = np.isin(status, ["approved", "active", "closed"])
    approved_at = pd.Series(pd.NaT, index=range(n)).to_numpy()
    approved_at = np.where(approved_mask,
                           pd.to_datetime(start_ts - rng.integers(7 * 86400, 30 * 86400, size=n), unit="s"),
                           np.datetime64("NaT"))
    return pd.DataFrame({
        "promotion_id": [f"PRM{i:08d}" for i in range(1, n + 1)],
        "account_id": accounts["account_id"].to_numpy()[a_idx],
        "name": [f"Q{fq_i} Promo {i:08d}" for i, fq_i in zip(range(1, n + 1), fq)],
        "fiscal_year": fy,
        "fiscal_quarter": fq,
        "start_date": pd.to_datetime(start_ts, unit="s").date,
        "end_date": pd.to_datetime(end_ts, unit="s").date,
        "ship_start_date": pd.to_datetime(ship_start_ts, unit="s").date,
        "ship_end_date": pd.to_datetime(ship_end_ts, unit="s").date,
        "status": status,
        "planned_spend_cents": planned_spend,
        "planned_volume_units": planned_volume,
        "planned_lift_pct": planned_lift,
        "forecast_roi": forecast_roi,
        "created_by": [f"user_{rng.integers(1, 500):03d}" for _ in range(n)],
        "created_at": created_at,
        "approved_at": approved_at,
    })


def _tactics(ctx, promotions, products, avg_per_promo=4):
    rng = ctx.rng
    n_promos = len(promotions)
    counts = rng.integers(1, avg_per_promo * 2, size=n_promos)
    n = int(counts.sum())
    promo_idx = np.repeat(np.arange(n_promos), counts)
    sub_promos = promotions.iloc[promo_idx].reset_index(drop=True)
    s_idx = rng.integers(0, len(products), size=n)
    sub_products = products.iloc[s_idx].reset_index(drop=True)
    discount = (sub_products["list_price_cents"].to_numpy() * rng.uniform(0.05, 0.30, size=n)).astype(np.int64)
    consumer_price = (sub_products["srp_cents"].to_numpy() * rng.uniform(0.65, 0.92, size=n)).astype(np.int64)
    planned_units = (rng.lognormal(6.0, 1.0, size=n)).astype(np.int64)
    planned_spend = (planned_units * discount).astype(np.int64)
    actual_units = (planned_units * rng.uniform(0.6, 1.6, size=n)).astype(np.int64)
    actual_spend = (actual_units * discount * rng.uniform(0.85, 1.15, size=n)).astype(np.int64)
    return pd.DataFrame({
        "tactic_id": [f"TAC{i:09d}" for i in range(1, n + 1)],
        "promotion_id": sub_promos["promotion_id"].to_numpy(),
        "sku_id": sub_products["sku_id"].to_numpy(),
        "tactic_type": weighted_choice(rng, TACTIC_TYPES, TACTIC_W, n),
        "discount_per_unit_cents": discount,
        "consumer_price_cents": consumer_price,
        "srp_cents": sub_products["srp_cents"].to_numpy(),
        "planned_units": planned_units,
        "planned_spend_cents": planned_spend,
        "actual_units": actual_units,
        "actual_spend_cents": actual_spend,
        "lift_expected_pct": np.round(rng.normal(35, 18, size=n).clip(-10, 200), 2),
        "feature_type": rng.choice(FEATURE_TYPES, size=n),
        "display_type": rng.choice(DISPLAY_TYPES, size=n),
        "tpr_only": rng.random(n) < 0.18,
        "settlement_method": rng.choice(SETTLEMENT_METHODS, size=n),
    })


def _deductions(ctx, accounts, tactics, n=50_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    matched_mask = rng.random(n) < 0.62
    t_idx = rng.integers(0, len(tactics), size=n)
    tactic_id = np.where(matched_mask, tactics["tactic_id"].to_numpy()[t_idx], None)
    amount = (rng.lognormal(7.0, 1.5, size=n) * 100).astype(np.int64)
    status = weighted_choice(rng, DEDUCTION_STATUS, DEDUCTION_STATUS_W, n)
    open_amount = np.where(np.isin(status, ["open", "matched", "disputed"]),
                           amount, 0).astype(np.int64)
    opened = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-01-01").timestamp()),
                     int(pd.Timestamp("2026-05-01").timestamp()), size=n),
        unit="s")
    aging = ((pd.Timestamp("2026-05-09") - opened).dt.days).clip(lower=0).astype(int)
    resolved_mask = np.isin(status, ["paid", "written_off", "chargeback_lost"])
    resolved_at = np.where(
        resolved_mask,
        opened + pd.to_timedelta(rng.integers(5, 180, size=n), unit="D"),
        np.datetime64("NaT"),
    )
    return pd.DataFrame({
        "deduction_id": [f"DED{i:08d}" for i in range(1, n + 1)],
        "account_id": accounts["account_id"].to_numpy()[a_idx],
        "invoice_id": [f"INV-{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "claim_number": [f"CLM-{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "tactic_id": tactic_id,
        "deduction_type": weighted_choice(rng, DEDUCTION_TYPES, DEDUCTION_TYPE_W, n),
        "amount_cents": amount,
        "open_amount_cents": open_amount,
        "opened_date": opened.dt.date,
        "aging_days": aging,
        "status": status,
        "dispute_reason": np.where(status == "disputed",
                                    rng.choice(DISPUTE_REASONS, size=n), None),
        "resolution_date": pd.to_datetime(resolved_at).date if hasattr(pd.to_datetime(resolved_at), 'date') else pd.Series(resolved_at).dt.date.to_numpy(),
        "validation_evidence_uri": [
            f"s3://tpm-evidence/{rng.integers(10**9, 10**10):010d}.pdf"
            if (mm and rng.random() < 0.7) else None
            for mm in matched_mask
        ],
    })


def _baseline_forecasts(ctx, accounts, products, weeks=104, account_sample=400, sku_sample=120):
    rng = ctx.rng
    sub_accounts = accounts.sample(n=account_sample, random_state=ctx.seed).reset_index(drop=True)
    sub_products = products.sample(n=sku_sample, random_state=ctx.seed + 1).reset_index(drop=True)
    week_starts = pd.date_range("2025-01-06", periods=weeks, freq="W-MON")
    n = len(sub_accounts) * len(sub_products) * len(week_starts)
    a_array = np.tile(np.repeat(sub_accounts["account_id"].to_numpy(), len(sub_products) * len(week_starts)), 1)
    s_array = np.tile(np.repeat(sub_products["sku_id"].to_numpy(), len(week_starts)), len(sub_accounts))
    w_array = np.tile(week_starts.values, len(sub_accounts) * len(sub_products))
    base_units = rng.lognormal(4.0, 0.8, size=n).astype(np.int64)
    base_dollars = (base_units * rng.uniform(50, 500, size=n)).astype(np.int64)
    model_idx = rng.integers(0, len(BASELINE_MODELS), size=n)
    return pd.DataFrame({
        "baseline_id": [f"BSL{i:09d}" for i in range(1, n + 1)],
        "account_id": a_array,
        "sku_id": s_array,
        "week_start_date": pd.to_datetime(w_array).date,
        "baseline_units": base_units,
        "baseline_dollars_cents": base_dollars,
        "model_name": [BASELINE_MODELS[i][0] for i in model_idx],
        "model_version": [BASELINE_MODELS[i][1] for i in model_idx],
        "confidence_band_low": (base_units * 0.85).astype(np.int64),
        "confidence_band_high": (base_units * 1.15).astype(np.int64),
        "generated_at": pd.to_datetime(w_array) + pd.Timedelta(days=2),
    })


def _lift_observations(ctx, tactics, accounts, products, n=300_000):
    rng = ctx.rng
    t_idx = rng.integers(0, len(tactics), size=n)
    sub_tactics = tactics.iloc[t_idx].reset_index(drop=True)
    a_idx = rng.integers(0, len(accounts), size=n)
    s_idx = rng.integers(0, len(products), size=n)
    actual = (rng.lognormal(5.0, 0.9, size=n)).astype(np.int64)
    baseline = (actual / rng.uniform(1.05, 2.5, size=n)).astype(np.int64).clip(min=1)
    incremental = (actual - baseline).clip(min=0).astype(np.int64)
    cannibalization = (incremental * rng.uniform(0.0, 0.30, size=n)).astype(np.int64)
    halo = (incremental * rng.uniform(0.0, 0.20, size=n)).astype(np.int64)
    inc_gp = (incremental * rng.integers(50, 800, size=n)).astype(np.int64)
    week = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-01-06").timestamp()),
                     int(pd.Timestamp("2026-05-04").timestamp()), size=n),
        unit="s").normalize()
    return pd.DataFrame({
        "lift_observation_id": [f"LFT{i:09d}" for i in range(1, n + 1)],
        "tactic_id": sub_tactics["tactic_id"].to_numpy(),
        "account_id": accounts["account_id"].to_numpy()[a_idx],
        "sku_id": products["sku_id"].to_numpy()[s_idx],
        "week_start_date": week.date,
        "actual_units": actual,
        "baseline_units": baseline,
        "incremental_units": incremental,
        "lift_pct": np.round((incremental / baseline) * 100, 2),
        "cannibalization_units": cannibalization,
        "halo_units": halo,
        "incremental_gross_profit_cents": inc_gp,
        "actual_roi": np.round(rng.normal(1.2, 0.9, size=n).clip(-1.0, 8.0), 2),
        "source": weighted_choice(rng, LIFT_SOURCES, LIFT_SOURCES_W, n),
    })


def _retailer_scan(ctx, accounts, outlets, products, n=2_000_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    o_idx = rng.integers(0, len(outlets), size=n)
    s_idx = rng.integers(0, len(products), size=n)
    sub_products = products.iloc[s_idx].reset_index(drop=True)
    units = rng.poisson(lam=12, size=n).astype(np.int64)
    avg_price = (sub_products["srp_cents"].to_numpy() * rng.uniform(0.70, 1.05, size=n)).astype(np.int64)
    dollars = (units * avg_price).astype(np.int64)
    on_promo = rng.random(n) < 0.18
    feature = on_promo & (rng.random(n) < 0.40)
    display = on_promo & (rng.random(n) < 0.35)
    tpr = on_promo & ~(feature | display)
    week = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-01-06").timestamp()),
                     int(pd.Timestamp("2026-05-04").timestamp()), size=n),
        unit="s").normalize()
    return pd.DataFrame({
        "scan_id": [f"SCN{i:010d}" for i in range(1, n + 1)],
        "account_id": accounts["account_id"].to_numpy()[a_idx],
        "outlet_id": outlets["outlet_id"].to_numpy()[o_idx],
        "sku_id": sub_products["sku_id"].to_numpy(),
        "gtin": sub_products["gtin"].to_numpy(),
        "week_start_date": week.date,
        "units_sold": units,
        "dollars_sold_cents": dollars,
        "avg_retail_price_cents": avg_price,
        "on_hand_units": rng.integers(0, 500, size=n).astype(np.int32),
        "on_promo_flag": on_promo,
        "feature_flag": feature,
        "display_flag": display,
        "tpr_flag": tpr,
        "source_doc": weighted_choice(rng, SCAN_SOURCES, SCAN_SOURCES_W, n),
        "ingested_at": week + pd.Timedelta(days=3),
    })


def _trade_funds(ctx, accounts, n=15_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    planned = (rng.lognormal(11.0, 1.2, size=n) * 100).astype(np.int64)
    committed = (planned * rng.uniform(0.5, 0.95, size=n)).astype(np.int64)
    spent = (committed * rng.uniform(0.3, 0.95, size=n)).astype(np.int64)
    return pd.DataFrame({
        "fund_id": [f"FND{i:07d}" for i in range(1, n + 1)],
        "account_id": accounts["account_id"].to_numpy()[a_idx],
        "brand": rng.choice(BRANDS, size=n),
        "fiscal_year": rng.choice([2025, 2026], size=n).astype("int16"),
        "fund_type": weighted_choice(rng, FUND_TYPES, FUND_TYPES_W, n),
        "planned_amount_cents": planned,
        "committed_amount_cents": committed,
        "spent_amount_cents": spent,
        "balance_cents": (planned - spent).astype(np.int64),
        "status": rng.choice(["active", "closed", "frozen"], p=[0.75, 0.20, 0.05], size=n),
    })


# ---------------------------------------------------------------------------
def generate(seed=42, scan_rows=2_000_000):
    ctx = make_context(seed)
    print("  generating accounts...")
    accounts = _accounts(ctx)
    print("  generating outlets...")
    outlets = _outlets(ctx, accounts)
    print("  generating products...")
    products = _products(ctx)
    print("  generating promotions (200k)...")
    promotions = _promotions(ctx, accounts)
    print("  generating tactics (~800k)...")
    tactics = _tactics(ctx, promotions, products)
    print("  generating deductions (50k)...")
    deductions = _deductions(ctx, accounts, tactics)
    print("  generating baseline_forecast (~5M cells; sampling 400 acct × 120 sku × 104 wk)...")
    baselines = _baseline_forecasts(ctx, accounts, products)
    print("  generating lift_observation (300k)...")
    lifts = _lift_observations(ctx, tactics, accounts, products)
    print(f"  generating retailer_scan_data ({scan_rows:,} rows)...")
    scan = _retailer_scan(ctx, accounts, outlets, products, n=scan_rows)
    print("  generating trade_fund (15k)...")
    funds = _trade_funds(ctx, accounts)

    tables = {
        "account": accounts,
        "customer_outlet": outlets,
        "product": products,
        "promotion": promotions,
        "promo_tactic": tactics,
        "deduction": deductions,
        "baseline_forecast": baselines,
        "lift_observation": lifts,
        "retailer_scan_data": scan,
        "trade_fund": funds,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--scan-rows", type=int, default=2_000_000,
                   help="Override retailer_scan_data row count for faster local runs.")
    args = p.parse_args()
    tables = generate(args.seed, scan_rows=args.scan_rows)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
