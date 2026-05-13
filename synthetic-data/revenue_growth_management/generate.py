"""
Synthetic Revenue Growth Management data — Vistex / Pricefx / Model N / PROS RGM
/ SAP S/4HANA RM + CCM / Anaplan PM / Periscope / BCG OS / Zilliant / Revenue
Analytics / Vendavo / Plytix PIM + Circana / NielsenIQ measurement.

Entities (>=10):
  account, product, pack, price_list, price_event, promo_plan, deal,
  baseline, mix_segment, sales_transaction.

Scale (deterministic, single seed):
  10,000 SKUs       × 1+ packs per SKU  (~14,000 packs total — entry/mainstream/premium ladder)
  100 accounts      × all packs ≈ price-list rows
  8 fiscal quarters of price events  -> ~240,000 price events
  ~200,000 deals    (multi-account × multi-pack × multi-tactic)
  ~100,000 baseline rows (account × pack × week × multiple models)
  100 promo plans   (one per account)
  ~1,000,000 sales_transaction rows (account × pack × day shipments)

Realism:
  - Long-tail account volume (Pareto sampling — Walmart/Costco dominate).
  - PPA ladder: entry/mainstream/premium/value/super tiers with stable benchmark margins.
  - Bi-temporal price events (announced_at vs effective_from).
  - Gross-to-net waterfall is computed line-by-line (off_invoice, rebate accrual,
    scan_down, bill_back, mcb, slotting, MDF) and reconciles to net_revenue_cents.
  - Promo periods generate spikier shipment weeks and tail forward-buy weeks.
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

SUBDOMAIN = "revenue_growth_management"

# -------------------------------- domain enums -------------------------------
CHANNELS = ["grocery", "mass", "club", "drug", "convenience", "dollar", "ecom", "food_service"]
CHANNEL_W = [0.28, 0.16, 0.10, 0.08, 0.14, 0.08, 0.10, 0.06]
CHANNEL_TIERS = ["premium", "mainstream", "value"]
CHANNEL_TIER_W = [0.18, 0.58, 0.24]

BRANDS = [
    "Olera", "Pinegrove", "Rivermark", "Cascadia", "Harvest Glen", "Northwind",
    "Solara", "Vivid Roast", "Crisp Hollow", "Glacier Bay", "Sunfield", "Bay Hill",
    "Granitestone", "Wildcrest", "Aurora Ridge", "Veridian", "Larkspur", "Maplehurst",
    "Tideline", "Quartzwood",
]
SUB_BRANDS = ["Classic", "Reserve", "Light", "Zero", "Plus", "Original", "Bold", "Smooth"]
CATEGORIES = ["Snacks", "Beverages", "Personal Care", "Pet Food", "Household", "Frozen", "Dairy", "Confections"]
SUBCATEGORIES_BY_CAT = {
    "Snacks": ["Salty", "Sweet", "Nuts", "Meat Snacks"],
    "Beverages": ["CSD", "Energy", "Water", "Juice", "Coffee Ready-to-Drink"],
    "Personal Care": ["Hair Care", "Skin Care", "Oral Care", "Deodorant"],
    "Pet Food": ["Dry Dog", "Wet Dog", "Dry Cat", "Wet Cat", "Treats"],
    "Household": ["Detergent", "Cleaners", "Paper Goods", "Air Care"],
    "Frozen": ["Pizza", "Entrees", "Sides", "Desserts"],
    "Dairy": ["Yogurt", "Cheese", "Milk Alternatives", "Cream"],
    "Confections": ["Chocolate", "Gum", "Mints", "Hard Candy"],
}
LIFECYCLE = ["intro", "grow", "core", "decline", "discontinued"]
LIFECYCLE_W = [0.06, 0.12, 0.72, 0.07, 0.03]

PACK_FORMATS = ["can", "bottle_pet", "bottle_glass", "carton", "pouch", "multipack", "value_pack", "super_pack"]
PPA_TIERS = ["entry", "mainstream", "premium", "value", "super"]
PPA_TIER_W = [0.18, 0.40, 0.20, 0.14, 0.08]

PRICE_EVENT_TYPES = ["list_increase", "list_decrease", "srp_change", "cost_change", "currency_revaluation"]
PRICE_EVENT_W = [0.52, 0.18, 0.16, 0.10, 0.04]
APPROVERS = ["VP_RGM", "RGM_Director", "CCO"]
APPROVER_W = [0.62, 0.30, 0.08]

TACTIC_TYPES = ["off_invoice", "scan_down", "bill_back", "mcb", "tpr", "feature", "display", "multibuy", "bogo", "coupon", "loyalty", "edlp"]
TACTIC_W = [0.22, 0.16, 0.10, 0.06, 0.14, 0.08, 0.06, 0.06, 0.04, 0.04, 0.02, 0.02]
MECHANICS = ["pct_off", "dollar_off", "2_for_X", "case_allowance", "conditional_rebate"]
MECHANIC_W = [0.32, 0.28, 0.14, 0.16, 0.10]
SETTLEMENTS = ["off_invoice", "deduction", "check", "emc", "edi820"]
SETTLEMENT_W = [0.38, 0.32, 0.10, 0.08, 0.12]

BASELINE_MODELS = ["circana_unify", "niq_baseline", "periscope_glm", "inhouse_ml", "pricefx_optimizer"]
BASELINE_W = [0.32, 0.26, 0.18, 0.16, 0.08]

SOURCE_SYSTEMS_PRICE = ["SAP_CCM", "Vistex", "Pricefx", "Model_N", "EDI_832", "manual"]
SOURCE_SYSTEMS_PRICE_W = [0.30, 0.26, 0.18, 0.12, 0.10, 0.04]
SOURCE_SYSTEMS_SALES = ["SAP_S4_SD", "Vistex", "Model_N"]
SOURCE_SYSTEMS_SALES_W = [0.78, 0.14, 0.08]

CURRENCIES = ["USD", "EUR", "GBP", "CAD", "MXN"]
CURRENCIES_W = [0.74, 0.10, 0.06, 0.06, 0.04]
COUNTRIES = ["US", "CA", "MX", "GB", "DE", "FR", "BR", "AU"]


# -------------------------------- generators ---------------------------------
def _accounts(ctx, n=100):
    rng = ctx.rng
    # Long-tail volume index seeded by Pareto so a handful dominate net revenue.
    return pd.DataFrame({
        "account_id":        [f"ACC{i:05d}" for i in range(1, n + 1)],
        "account_name":      [ctx.faker.company() for _ in range(n)],
        "parent_account_id": np.where(rng.random(n) < 0.30,
                                       [f"ACC{rng.integers(1, n + 1):05d}" for _ in range(n)],
                                       None),
        "channel":           weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "channel_tier":      weighted_choice(rng, CHANNEL_TIERS, CHANNEL_TIER_W, n),
        "country_iso2":      rng.choice(COUNTRIES, size=n),
        "gln":               [f"{rng.integers(10**12, 10**13):013d}" for _ in range(n)],
        "status":            weighted_choice(rng, ["active", "paused", "discontinued"], [0.94, 0.04, 0.02], n),
        "created_at":        pd.to_datetime(
            rng.integers(int(pd.Timestamp("2018-01-01").timestamp()),
                         int(pd.Timestamp("2025-01-01").timestamp()), size=n),
            unit="s"),
    })


def _products(ctx, n=10_000):
    rng = ctx.rng
    brand = rng.choice(BRANDS, size=n)
    sub_brand = rng.choice(SUB_BRANDS, size=n)
    category = rng.choice(CATEGORIES, size=n)
    subcategory = np.array([rng.choice(SUBCATEGORIES_BY_CAT[c]) for c in category])
    launch = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2015-01-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s",
    ).normalize()
    innovation = (pd.Timestamp("2026-05-01") - launch).days <= 730
    return pd.DataFrame({
        "sku_id":          [f"SKU{i:07d}" for i in range(1, n + 1)],
        "gtin":            [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "brand":           brand,
        "sub_brand":       sub_brand,
        "category":        category,
        "subcategory":     subcategory,
        # Cost of goods per case in cents — lognormal $5-$60.
        "cogs_cents":      (rng.lognormal(7.0, 0.9, size=n) * 100).astype(np.int64).clip(100, 1_500_000),
        "launch_date":     launch.date,
        "lifecycle_stage": weighted_choice(rng, LIFECYCLE, LIFECYCLE_W, n),
        "innovation_flag": innovation,
        "status":          weighted_choice(rng, ["active", "paused", "discontinued"], [0.93, 0.04, 0.03], n),
    })


def _packs(ctx, products, packs_per_sku=1.4):
    """Build the PPA ladder. Each SKU gets 1-3 packs across tiers."""
    rng = ctx.rng
    rows = []
    pack_seq = 1
    for sku_id, cogs in zip(products["sku_id"].to_numpy(), products["cogs_cents"].to_numpy()):
        n_packs = int(rng.choice([1, 2, 3], p=[0.40, 0.40, 0.20]))
        # Pick tiers without replacement among the canonical 5.
        tiers = list(rng.choice(PPA_TIERS, size=n_packs, replace=False))
        for tier_idx, tier in enumerate(tiers, start=1):
            size_count = {
                "entry":      int(rng.choice([1, 2, 4, 6])),
                "mainstream": int(rng.choice([6, 8, 12])),
                "premium":    int(rng.choice([6, 8, 12, 24])),
                "value":      int(rng.choice([12, 18, 24])),
                "super":      int(rng.choice([24, 30, 36, 48])),
            }[tier]
            tier_margin_multiplier = {
                "entry": 0.18, "mainstream": 0.30, "premium": 0.42, "value": 0.20, "super": 0.16
            }[tier]
            tier_price_multiplier = {
                "entry": 1.0, "mainstream": 1.6, "premium": 2.4, "value": 2.0, "super": 3.0
            }[tier]
            benchmark_net = int(cogs * (1.0 + tier_margin_multiplier) * tier_price_multiplier)
            benchmark_margin = int(benchmark_net - cogs * tier_price_multiplier)
            rows.append({
                "pack_id":                       f"PCK{pack_seq:08d}",
                "sku_id":                        sku_id,
                "pack_name":                     f"{sku_id} {tier} {size_count}-{rng.choice(['pk','ct','pkg'])}",
                "pack_size_count":               size_count,
                "pack_format":                   str(rng.choice(PACK_FORMATS)),
                "ppa_tier":                      tier,
                "ladder_rank":                   tier_idx,
                "benchmark_net_price_cents":     benchmark_net,
                "benchmark_margin_cents":        benchmark_margin,
                "launch_date":                   pd.Timestamp(
                    rng.integers(int(pd.Timestamp("2017-01-01").timestamp()),
                                  int(pd.Timestamp("2026-04-01").timestamp()))
                    , unit="s").date(),
                "status":                        str(rng.choice(["active", "paused", "discontinued"], p=[0.93, 0.04, 0.03])),
            })
            pack_seq += 1
    return pd.DataFrame(rows)


def _price_list(ctx, accounts, packs, n=200_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    p_idx = rng.integers(0, len(packs), size=n)
    eff_from = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                     int(pd.Timestamp("2026-05-01").timestamp()), size=n),
        unit="s").normalize()
    ttl_days = rng.integers(60, 365, size=n)
    eff_to = eff_from + pd.to_timedelta(ttl_days, unit="D")
    benchmark = packs["benchmark_net_price_cents"].to_numpy()[p_idx]
    list_price = (benchmark * rng.uniform(1.05, 1.35, size=n)).astype(np.int64)
    srp = (list_price * rng.uniform(1.30, 1.85, size=n)).astype(np.int64)
    return pd.DataFrame({
        "price_list_id":    [f"PL{i:010d}" for i in range(1, n + 1)],
        "account_id":       accounts["account_id"].to_numpy()[a_idx],
        "pack_id":          packs["pack_id"].to_numpy()[p_idx],
        "list_price_cents": list_price,
        "srp_cents":        srp,
        "currency":         weighted_choice(rng, CURRENCIES, CURRENCIES_W, n),
        "effective_from":   eff_from.date,
        "effective_to":     eff_to.date,
        "recorded_at":      eff_from + pd.to_timedelta(rng.integers(-7, 60, size=n), unit="D"),
        "source_system":    weighted_choice(rng, SOURCE_SYSTEMS_PRICE, SOURCE_SYSTEMS_PRICE_W, n),
        "status":           weighted_choice(rng, ["active", "superseded", "draft"], [0.78, 0.18, 0.04], n),
    })


def _price_events(ctx, accounts, packs, n=240_000):
    """8 quarters × ~3 price events per account × pack tier ≈ 240k events."""
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    p_idx = rng.integers(0, len(packs), size=n)
    benchmark = packs["benchmark_net_price_cents"].to_numpy()[p_idx]
    prior = (benchmark * rng.uniform(1.00, 1.30, size=n)).astype(np.int64)
    # Most are inflation-tracking small increases; rare big decreases / structural moves.
    direction = weighted_choice(rng, PRICE_EVENT_TYPES, PRICE_EVENT_W, n)
    delta_pct = np.where(direction == "list_increase",
                         rng.uniform(0.005, 0.10, size=n),
                         np.where(direction == "list_decrease",
                                  -rng.uniform(0.005, 0.15, size=n),
                                  rng.uniform(-0.05, 0.05, size=n)))
    new_list = (prior * (1 + delta_pct)).astype(np.int64).clip(min=1)
    prior_srp = (prior * rng.uniform(1.35, 1.80, size=n)).astype(np.int64)
    new_srp = (new_list * rng.uniform(1.30, 1.85, size=n)).astype(np.int64)
    announced = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-04-01").timestamp()),
                     int(pd.Timestamp("2026-05-01").timestamp()), size=n),
        unit="s")
    effective = (announced + pd.to_timedelta(rng.integers(0, 90, size=n), unit="D")).normalize()
    return pd.DataFrame({
        "price_event_id":         [f"PE{i:010d}" for i in range(1, n + 1)],
        "account_id":             accounts["account_id"].to_numpy()[a_idx],
        "pack_id":                packs["pack_id"].to_numpy()[p_idx],
        "event_type":             direction,
        "prior_list_price_cents": prior,
        "new_list_price_cents":   new_list,
        "prior_srp_cents":        prior_srp,
        "new_srp_cents":          new_srp,
        "currency":               weighted_choice(rng, CURRENCIES, CURRENCIES_W, n),
        "announced_at":           announced,
        "effective_from":         effective.date,
        "source_system":          weighted_choice(rng, SOURCE_SYSTEMS_PRICE, SOURCE_SYSTEMS_PRICE_W, n),
        "approver_role":          weighted_choice(rng, APPROVERS, APPROVER_W, n),
    })


def _promo_plans(ctx, accounts, n=100):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    plan_brand = rng.choice(BRANDS, size=n)
    fiscal_year = rng.choice([2024, 2025, 2026], size=n, p=[0.20, 0.45, 0.35])
    fiscal_quarter = rng.choice([1, 2, 3, 4], size=n)
    planned_nr = (rng.lognormal(13.0, 1.0, size=n) * 100).astype(np.int64)
    planned_trade = (planned_nr * rng.uniform(0.08, 0.22, size=n)).astype(np.int64)
    planned_vol = (planned_nr / rng.uniform(800, 5_000, size=n)).astype(np.int64).clip(min=10)
    created = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-06-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s")
    approved = created + pd.to_timedelta(rng.integers(1, 90, size=n), unit="D")
    return pd.DataFrame({
        "promo_plan_id":             [f"PLN{i:06d}" for i in range(1, n + 1)],
        "account_id":                accounts["account_id"].to_numpy()[a_idx],
        "name":                      [f"{plan_brand[i]} {['Holiday','Spring','Summer','Back-to-School','Q1','Q2','Q3','Q4'][int(rng.integers(0, 8))]} Plan {fiscal_year[i]}" for i in range(n)],
        "brand":                     plan_brand,
        "fiscal_year":               fiscal_year.astype("int16"),
        "fiscal_quarter":            fiscal_quarter.astype("int16"),
        "planned_net_revenue_cents": planned_nr,
        "planned_trade_spend_cents": planned_trade,
        "planned_volume_units":      planned_vol,
        "forecast_roi":              np.round(rng.uniform(0.4, 3.5, size=n), 2),
        "status":                    weighted_choice(rng, ["draft", "approved", "in_market", "closed", "cancelled"], [0.04, 0.14, 0.34, 0.42, 0.06], n),
        "created_by":                [ctx.faker.user_name() for _ in range(n)],
        "created_at":                created,
        "approved_at":               approved,
    })


def _deals(ctx, plans, packs, n=200_000):
    rng = ctx.rng
    pln_idx = rng.integers(0, len(plans), size=n)
    p_idx = rng.integers(0, len(packs), size=n)
    sub_plans = plans.iloc[pln_idx].reset_index(drop=True)
    benchmark = packs["benchmark_net_price_cents"].to_numpy()[p_idx]
    tactic = weighted_choice(rng, TACTIC_TYPES, TACTIC_W, n)
    discount_pct = rng.uniform(0.05, 0.40, size=n)
    discount_per_unit = (benchmark * discount_pct).astype(np.int64)
    rebate_pct = np.round(rng.uniform(0.0, 0.12, size=n), 4)
    deal_floor = (benchmark * rng.uniform(0.45, 0.85, size=n)).astype(np.int64)
    planned_units = (rng.lognormal(8.0, 1.0, size=n)).astype(np.int64).clip(min=10)
    planned_spend = (planned_units * discount_per_unit).astype(np.int64)
    # Actual lands within ±35% of plan with a forward-buy tail (positive skew).
    actual_units = (planned_units * rng.uniform(0.55, 1.45, size=n) +
                    rng.gamma(2.0, 50, size=n) * (rng.random(n) < 0.20)).astype(np.int64)
    actual_spend = (actual_units * discount_per_unit).astype(np.int64)
    forward_buy = (actual_units * rng.uniform(0.0, 0.18, size=n) * discount_per_unit).astype(np.int64)
    start = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-10-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s").normalize()
    duration_d = rng.integers(7, 56, size=n)
    end = start + pd.to_timedelta(duration_d, unit="D")
    return pd.DataFrame({
        "deal_id":                  [f"DL{i:010d}" for i in range(1, n + 1)],
        "promo_plan_id":            sub_plans["promo_plan_id"].to_numpy(),
        "account_id":               sub_plans["account_id"].to_numpy(),
        "pack_id":                  packs["pack_id"].to_numpy()[p_idx],
        "tactic_type":              tactic,
        "mechanic":                 weighted_choice(rng, MECHANICS, MECHANIC_W, n),
        "discount_per_unit_cents":  discount_per_unit,
        "rebate_pct":               rebate_pct,
        "deal_floor_cents":         deal_floor,
        "planned_units":            planned_units,
        "planned_spend_cents":      planned_spend,
        "actual_units":              actual_units,
        "actual_spend_cents":       actual_spend,
        "forward_buy_cost_cents":   forward_buy,
        "start_date":               start.date,
        "end_date":                 end.date,
        "settlement_method":        weighted_choice(rng, SETTLEMENTS, SETTLEMENT_W, n),
        "status":                   weighted_choice(rng, ["draft", "approved", "in_market", "settled", "cancelled"], [0.04, 0.12, 0.28, 0.50, 0.06], n),
    })


def _baselines(ctx, accounts, packs, n=100_000):
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    p_idx = rng.integers(0, len(packs), size=n)
    benchmark = packs["benchmark_net_price_cents"].to_numpy()[p_idx]
    base_units = rng.gamma(2.0, 400, size=n).astype(np.int64).clip(min=1)
    base_revenue = (base_units * benchmark).astype(np.int64)
    week = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-06-01").timestamp()),
                     int(pd.Timestamp("2026-05-01").timestamp()), size=n),
        unit="s").normalize()
    ci_lo = (base_units * rng.uniform(0.78, 0.94, size=n)).astype(np.int64)
    ci_hi = (base_units * rng.uniform(1.06, 1.22, size=n)).astype(np.int64)
    return pd.DataFrame({
        "baseline_id":                  [f"BL{i:010d}" for i in range(1, n + 1)],
        "account_id":                   accounts["account_id"].to_numpy()[a_idx],
        "pack_id":                      packs["pack_id"].to_numpy()[p_idx],
        "week_start_date":              week.date,
        "baseline_units":               base_units,
        "baseline_net_revenue_cents":   base_revenue,
        "model_name":                   weighted_choice(rng, BASELINE_MODELS, BASELINE_W, n),
        "model_version":                rng.choice(["v1.4", "v2.0", "v2.1", "v3.0"], size=n),
        "confidence_band_low_units":    ci_lo,
        "confidence_band_high_units":   ci_hi,
        "generated_at":                 week + pd.to_timedelta(rng.integers(1, 14, size=n), unit="D"),
    })


def _mix_segments(ctx):
    rng = ctx.rng
    rows = []
    seq = 1
    for ch in CHANNELS:
        for tier in PPA_TIERS:
            for cat in CATEGORIES:
                rows.append({
                    "segment_id":                          f"SEG{seq:05d}",
                    "channel":                             ch,
                    "ppa_tier":                            tier,
                    "category":                            cat,
                    "target_share_pct":                    float(np.round(rng.uniform(0.005, 0.18), 4)),
                    "target_net_revenue_per_unit_cents":   int(rng.lognormal(7.5, 0.6)) * 10,
                })
                seq += 1
    return pd.DataFrame(rows)


def _sales_transactions(ctx, accounts, packs, deals, n=1_000_000):
    """1M sales transactions — account × pack × day shipment fact."""
    rng = ctx.rng
    a_idx = rng.integers(0, len(accounts), size=n)
    p_idx = rng.integers(0, len(packs), size=n)
    benchmark = packs["benchmark_net_price_cents"].to_numpy()[p_idx]
    units = rng.gamma(2.0, 80, size=n).astype(np.int64).clip(min=1)
    gross = (units * benchmark * rng.uniform(1.05, 1.30, size=n)).astype(np.int64)
    # Trade lines — most rows have at least one trade contributor; clean off the rest.
    off_invoice = (gross * np.where(rng.random(n) < 0.42, rng.uniform(0.02, 0.18, size=n), 0)).astype(np.int64)
    rebate = (gross * np.where(rng.random(n) < 0.55, rng.uniform(0.01, 0.10, size=n), 0)).astype(np.int64)
    scan_down = (gross * np.where(rng.random(n) < 0.30, rng.uniform(0.005, 0.08, size=n), 0)).astype(np.int64)
    bill_back = (gross * np.where(rng.random(n) < 0.18, rng.uniform(0.005, 0.06, size=n), 0)).astype(np.int64)
    mcb = (gross * np.where(rng.random(n) < 0.10, rng.uniform(0.01, 0.04, size=n), 0)).astype(np.int64)
    slotting = (gross * np.where(rng.random(n) < 0.04, rng.uniform(0.001, 0.012, size=n), 0)).astype(np.int64)
    mdf = (gross * np.where(rng.random(n) < 0.14, rng.uniform(0.001, 0.018, size=n), 0)).astype(np.int64)
    total_gtn = off_invoice + rebate + scan_down + bill_back + mcb + slotting + mdf
    net = (gross - total_gtn).astype(np.int64).clip(min=0)
    cogs = (units * packs["benchmark_net_price_cents"].to_numpy()[p_idx] *
            rng.uniform(0.42, 0.74, size=n)).astype(np.int64)
    invoice_date = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-06-01").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s").normalize()
    # ~62% of sales are tied to a deal; rest are base shipments.
    has_deal = rng.random(n) < 0.62
    deal_ids_sample = rng.choice(deals["deal_id"].to_numpy(), size=n)
    return pd.DataFrame({
        "transaction_id":             [f"TX{i:011d}" for i in range(1, n + 1)],
        "account_id":                 accounts["account_id"].to_numpy()[a_idx],
        "pack_id":                    packs["pack_id"].to_numpy()[p_idx],
        "deal_id":                    np.where(has_deal, deal_ids_sample, None),
        "invoice_date":               invoice_date.date,
        "units":                      units,
        "gross_revenue_cents":        gross,
        "off_invoice_cents":          off_invoice,
        "rebate_accrual_cents":       rebate,
        "scan_down_cents":            scan_down,
        "bill_back_cents":            bill_back,
        "mcb_cents":                  mcb,
        "slotting_cents":             slotting,
        "marketing_dev_funds_cents":  mdf,
        "net_revenue_cents":          net,
        "cogs_cents":                 cogs,
        "currency":                   weighted_choice(rng, CURRENCIES, CURRENCIES_W, n),
        "source_system":              weighted_choice(rng, SOURCE_SYSTEMS_SALES, SOURCE_SYSTEMS_SALES_W, n),
    })


# -------------------------------- driver -------------------------------------
def generate(seed=42):
    ctx = make_context(seed)
    print("  generating accounts...")
    accounts = _accounts(ctx)
    print("  generating products...")
    products = _products(ctx)
    print("  generating packs (PPA ladder)...")
    packs = _packs(ctx, products)
    print(f"  -> {len(packs):,} packs")
    print("  generating price_list...")
    price_list = _price_list(ctx, accounts, packs)
    print("  generating price_events (~240k)...")
    price_events = _price_events(ctx, accounts, packs)
    print("  generating promo_plans...")
    promo_plans = _promo_plans(ctx, accounts)
    print("  generating deals (~200k)...")
    deals = _deals(ctx, promo_plans, packs)
    print("  generating baselines (~100k)...")
    baselines = _baselines(ctx, accounts, packs)
    print("  generating mix_segments...")
    mix_segments = _mix_segments(ctx)
    print("  generating sales_transactions (~1M)...")
    sales = _sales_transactions(ctx, accounts, packs, deals)
    tables = {
        "account":           accounts,
        "product":           products,
        "pack":              packs,
        "price_list":        price_list,
        "price_event":       price_events,
        "promo_plan":        promo_plans,
        "deal":              deals,
        "baseline":          baselines,
        "mix_segment":       mix_segments,
        "sales_transaction": sales,
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
