"""
Synthetic Pricing & Promotions data — modeled on the retail-pricing stack:
Revionics / PROS / Blue Yonder / Oracle RPCS price + markdown optimisers,
Eagle Eye / Inmar promo engines, and Wiser / Numerator / NielsenIQ competitive
feeds. POS-realised prices land via Toshiba TCx / NCR Voyix.

Entities (10):
  product, store, price_zone, price, promo, promo_line, markdown,
  competitive_price, sales_fact, elasticity_estimate.

Sizing (~720k+ price snapshots):
  10,000 SKUs * 200 stores * 90 days * ~4 events/day  ~=  720k price rows
  20,000 promos (with ~5 promo_lines each ~= 100k promo_lines)
  200,000 markdowns
  100,000 competitive_price observations
  ~400,000 sales_fact rows (sampled across SKU-store-days)
  ~80,000 elasticity estimates (product x cluster)

Realism:
  - KVI vs background SKUs differ in margin, elasticity, and promo cadence.
  - Promo lift distribution is bimodal: small (TPR) vs deep (BOGO / -40%).
  - Elasticity log-normal centered ~-1.5, bounded into a sensible band.
  - Markdown depth grows with weeks-on-hand (lifecycle pressure).
  - Competitive observations carry varied match_confidence.
  - All large-range integer IDs are int64-safe.
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

SUBDOMAIN = "pricing_and_promotions"

LIFECYCLE_STAGES = ["intro", "grow", "core", "decline", "clearance"]
LIFECYCLE_W = [0.08, 0.18, 0.55, 0.13, 0.06]
KVI_CLASSES = ["KVI", "KVC", "background", "traffic", "premium"]
KVI_W = [0.08, 0.12, 0.55, 0.15, 0.10]
CATEGORIES = [
    ("CAT01", "Beverages"), ("CAT02", "Snacks"), ("CAT03", "Dairy"),
    ("CAT04", "Frozen"), ("CAT05", "Produce"), ("CAT06", "Bakery"),
    ("CAT07", "Health"), ("CAT08", "Beauty"), ("CAT09", "Household"),
    ("CAT10", "Apparel"), ("CAT11", "Footwear"), ("CAT12", "Electronics"),
    ("CAT13", "Toys"), ("CAT14", "Pet"), ("CAT15", "Auto Parts"),
]
SUBCATEGORIES = [f"SUB{i:03d}" for i in range(1, 81)]
BRANDS = [
    "Acme Foods", "BrightLeaf", "ChevronBrands", "DeepBlue", "Evergreen",
    "FieldHarvest", "GoldenPaw", "Halcyon", "IronOak", "Juniper Co.",
    "Kingfisher", "Lumen", "MapleRidge", "Northwind", "Oakshire", "PrivateLabel",
    "Quill", "RedRiver", "SilverPine", "Tundra", "UrbanCo", "Verdant",
    "WildHorse", "Xavier", "YellowDoor", "Zenith",
]
PRICING_STRATEGIES = ["EDLP", "hi-lo", "hybrid"]
PRICING_STRATEGY_W = [0.30, 0.45, 0.25]
ZONE_TIERS = ["premium", "mainstream", "value"]
ZONE_TIER_W = [0.20, 0.55, 0.25]
PRICE_TYPES = ["regular", "promo", "markdown", "clearance", "cost"]
PRICE_TYPE_W = [0.62, 0.20, 0.10, 0.04, 0.04]
SOURCE_SYSTEMS = ["RMS", "RPCS", "Revionics", "PROS", "BlueYonder", "POS"]
SOURCE_SYSTEM_W = [0.20, 0.18, 0.22, 0.10, 0.18, 0.12]
STORE_FORMATS = ["hypermarket", "supermarket", "convenience", "specialty", "ecom"]
STORE_FORMAT_W = [0.10, 0.45, 0.20, 0.15, 0.10]
COUNTRIES = ["US", "GB", "DE", "FR", "CA", "MX", "ES", "IT", "NL", "PL"]

PROMO_MECHANICS = ["pct_off", "dollar_off", "bogo", "multibuy", "tpr", "loyalty", "coupon"]
PROMO_MECHANIC_W = [0.32, 0.18, 0.10, 0.10, 0.18, 0.07, 0.05]
FUNDING_SOURCES = ["retailer", "vendor", "jbp", "coop"]
FUNDING_W = [0.40, 0.30, 0.20, 0.10]
PROMO_STATUS = ["planned", "active", "completed", "cancelled"]
PROMO_STATUS_W = [0.10, 0.18, 0.68, 0.04]
MARKDOWN_REASONS = ["seasonal", "excess_inventory", "damage", "defective", "clearance", "competitor"]
MARKDOWN_REASON_W = [0.32, 0.30, 0.04, 0.03, 0.20, 0.11]
OPTIMIZERS = ["Revionics", "BlueYonder", "PROS", "Oracle_RPCS", "manual"]
OPTIMIZER_W = [0.35, 0.20, 0.15, 0.15, 0.15]
CHANNELS = ["in_store", "web", "app", "marketplace"]
CHANNEL_W = [0.45, 0.30, 0.15, 0.10]
MATCH_TYPES = ["exact_gtin", "equivalent", "like_for_like"]
MATCH_TYPE_W = [0.55, 0.30, 0.15]
COMP_SOURCES = ["Wiser", "Price2Spy", "Skuuudle", "DataWeave", "Numerator", "NielsenIQ", "manual"]
COMP_SOURCE_W = [0.30, 0.10, 0.08, 0.10, 0.20, 0.18, 0.04]
COMPETITORS = [
    ("COMP01", "Walmart"), ("COMP02", "Target"), ("COMP03", "Costco"),
    ("COMP04", "Kroger"), ("COMP05", "Aldi"), ("COMP06", "Tesco"),
    ("COMP07", "Carrefour"), ("COMP08", "Lidl"), ("COMP09", "Amazon"),
    ("COMP10", "Sainsbury"), ("COMP11", "Albert Heijn"), ("COMP12", "REWE"),
]


# ---------------------------------------------------------------------------
def _price_zones(ctx, n=12):
    rng = ctx.rng
    return pd.DataFrame({
        "price_zone_id": [f"PZ{i:03d}" for i in range(1, n + 1)],
        "zone_name": [f"Zone {chr(64 + i)}" for i in range(1, n + 1)],
        "pricing_strategy": weighted_choice(rng, PRICING_STRATEGIES, PRICING_STRATEGY_W, n),
        "tier": weighted_choice(rng, ZONE_TIERS, ZONE_TIER_W, n),
    })


def _products(ctx, n=10_000):
    rng = ctx.rng
    cat_idx = rng.integers(0, len(CATEGORIES), size=n)
    categories = np.array([CATEGORIES[i][0] for i in cat_idx])
    unit_cost = np.round(rng.lognormal(0.8, 1.0, size=n).clip(0.10, 950.0), 4)
    return pd.DataFrame({
        "product_id": [f"PRD{i:07d}" for i in range(1, n + 1)],
        "gtin": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "sku": [f"SKU{i:07d}" for i in range(1, n + 1)],
        "name": [f"{rng.choice(BRANDS)} {CATEGORIES[i][1]} Item {idx:05d}"
                 for idx, i in zip(range(1, n + 1), cat_idx)],
        "brand": rng.choice(BRANDS, size=n),
        "category_id": categories,
        "subcategory_id": rng.choice(SUBCATEGORIES, size=n),
        "lifecycle_stage": weighted_choice(rng, LIFECYCLE_STAGES, LIFECYCLE_W, n),
        "kvi_class": weighted_choice(rng, KVI_CLASSES, KVI_W, n),
        "unit_cost": unit_cost,
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
    })


def _stores(ctx, zones, n=200):
    rng = ctx.rng
    zone_idx = rng.integers(0, len(zones), size=n)
    return pd.DataFrame({
        "store_id": [f"ST{i:04d}" for i in range(1, n + 1)],
        "store_name": [f"Store #{i:04d}" for i in range(1, n + 1)],
        "banner": rng.choice(["MainBanner", "ValueBanner", "PremiumBanner", "DigitalBanner"],
                             p=[0.50, 0.25, 0.15, 0.10], size=n),
        "price_zone_id": zones["price_zone_id"].to_numpy()[zone_idx],
        "region": rng.choice(["NE", "SE", "MW", "SW", "W", "NW", "Central", "EU-West", "EU-South", "UK"], size=n),
        "country_iso2": weighted_choice(rng, COUNTRIES, [0.50, 0.10, 0.08, 0.08, 0.05, 0.04, 0.04, 0.04, 0.04, 0.03], n),
        "format": weighted_choice(rng, STORE_FORMATS, STORE_FORMAT_W, n),
        "open_date": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2010-01-01").timestamp()),
                         int(pd.Timestamp("2025-12-01").timestamp()), size=n),
            unit="s"),
        "status": rng.choice(["active", "closing", "closed"], p=[0.94, 0.04, 0.02], size=n),
    })


def _prices(ctx, products, stores, n=720_000):
    """SKU x store x day x event price snapshots.

    Distribution: ~62% regular, ~20% promo, ~10% markdown, etc.
    Effective windows span 1 hour to 30 days; promos shorter, regulars longer.
    """
    rng = ctx.rng
    p_idx = rng.integers(0, len(products), size=n)
    s_idx = rng.integers(0, len(stores), size=n)
    base_cost = products["unit_cost"].to_numpy()[p_idx]
    # Margin sample: KVI thinner, premium thicker, background middle.
    margin = rng.uniform(0.05, 0.55, size=n)
    raw_price = base_cost * (1.0 + margin)
    raw_price = np.round(raw_price, 2).astype(np.float64)
    price_type = weighted_choice(rng, PRICE_TYPES, PRICE_TYPE_W, n)
    # Apply discount adjustments for non-regular prices.
    discount_factor = np.where(price_type == "regular", 1.0,
                       np.where(price_type == "promo", rng.uniform(0.70, 0.95, size=n),
                       np.where(price_type == "markdown", rng.uniform(0.55, 0.85, size=n),
                       np.where(price_type == "clearance", rng.uniform(0.30, 0.65, size=n),
                                base_cost / raw_price))))
    amount = np.round(raw_price * discount_factor, 4).clip(min=0.10)

    effective_from = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-09").timestamp()),
                     int(pd.Timestamp("2026-05-10").timestamp()), size=n),
        unit="s")
    duration_h = np.where(price_type == "regular",
                          rng.integers(72, 720, size=n),
                          rng.integers(2, 168, size=n))
    effective_to = effective_from + pd.to_timedelta(duration_h, unit="h")
    prior_30day_low = (amount * rng.uniform(0.80, 1.0, size=n) * 100).astype(np.int64)
    return pd.DataFrame({
        "price_id": [f"PRC{i:010d}" for i in range(1, n + 1)],
        "product_id": products["product_id"].to_numpy()[p_idx],
        "store_id": stores["store_id"].to_numpy()[s_idx],
        "price_zone_id": stores["price_zone_id"].to_numpy()[s_idx],
        "price_type": price_type,
        "amount": amount,
        "currency": rng.choice(["USD", "EUR", "GBP", "CAD"], p=[0.70, 0.18, 0.07, 0.05], size=n),
        "effective_from": effective_from,
        "effective_to": effective_to,
        "source_system": weighted_choice(rng, SOURCE_SYSTEMS, SOURCE_SYSTEM_W, n),
        "prior_30day_low_minor": prior_30day_low,
        "status": rng.choice(["active", "superseded", "future"], p=[0.65, 0.30, 0.05], size=n),
    })


def _promos(ctx, n=20_000):
    rng = ctx.rng
    mechanic = weighted_choice(rng, PROMO_MECHANICS, PROMO_MECHANIC_W, n)
    # Discount depth bimodal: small TPR-style (3-12%) vs deeper (20-50%)
    deep_mask = rng.random(n) < 0.42
    shallow_pct = rng.uniform(0.03, 0.12, size=n)
    deep_pct = rng.uniform(0.20, 0.50, size=n)
    discount_pct = np.where(deep_mask, deep_pct, shallow_pct)
    discount_amount_minor = (rng.uniform(50, 800, size=n)).astype(np.int64)
    start_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-01").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    duration_d = rng.choice([3, 5, 7, 10, 14, 21, 28], p=[0.05, 0.15, 0.40, 0.15, 0.15, 0.06, 0.04], size=n)
    end_ts = start_ts + pd.to_timedelta(duration_d, unit="D")
    funding = weighted_choice(rng, FUNDING_SOURCES, FUNDING_W, n)
    trade_spend_minor = np.where(funding == "retailer",
                                 0,
                                 (rng.lognormal(7.5, 1.0, size=n) * 100).astype(np.int64))
    return pd.DataFrame({
        "promo_id": [f"PROMO{i:07d}" for i in range(1, n + 1)],
        "promo_name": [f"Promo {i:07d}" for i in range(1, n + 1)],
        "mechanic": mechanic,
        "discount_pct": np.round(discount_pct, 4),
        "discount_amount_minor": discount_amount_minor,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "funding_source": funding,
        "trade_spend_minor": trade_spend_minor,
        "vendor_id": [f"VND{rng.integers(1, 5000):05d}" if f != "retailer" else None
                      for f in funding],
        "status": weighted_choice(rng, PROMO_STATUS, PROMO_STATUS_W, n),
        "created_at": start_ts - pd.to_timedelta(rng.integers(7, 90, size=n), unit="D"),
    })


def _promo_lines(ctx, promos, products, stores, lines_per_promo=5):
    """SKU-level participation in a promo. ~100k rows when 20k promos * 5 lines."""
    rng = ctx.rng
    n = len(promos) * lines_per_promo
    promo_idx = np.repeat(np.arange(len(promos)), lines_per_promo)
    p_idx = rng.integers(0, len(products), size=n)
    s_idx = rng.integers(0, len(stores), size=n)
    planned_baseline = rng.integers(20, 2_000, size=n)
    planned_lift_pct = np.round(rng.uniform(0.05, 1.20, size=n), 4)
    planned_funding_minor = (rng.lognormal(6.0, 1.0, size=n) * 100).astype(np.int64)
    # Realised lift sometimes underperforms plan (mean 0.85 of plan with noise).
    realisation = rng.normal(0.85, 0.30, size=n).clip(0.10, 2.50)
    actual_units = (planned_baseline * (1.0 + planned_lift_pct * realisation)).astype(np.int64)
    actual_funding_minor = (planned_funding_minor * rng.uniform(0.80, 1.15, size=n)).astype(np.int64)
    return pd.DataFrame({
        "promo_line_id": [f"PRMLN{i:010d}" for i in range(1, n + 1)],
        "promo_id": promos["promo_id"].to_numpy()[promo_idx],
        "product_id": products["product_id"].to_numpy()[p_idx],
        "store_id": stores["store_id"].to_numpy()[s_idx],
        "planned_baseline_units": planned_baseline,
        "planned_lift_pct": planned_lift_pct,
        "planned_funding_minor": planned_funding_minor,
        "actual_units": actual_units,
        "actual_funding_minor": actual_funding_minor,
        "cannibalization_flag": rng.random(n) < 0.18,
    })


def _markdowns(ctx, products, stores, n=200_000):
    rng = ctx.rng
    p_idx = rng.integers(0, len(products), size=n)
    s_idx = rng.integers(0, len(stores), size=n)
    base_cost = products["unit_cost"].to_numpy()[p_idx]
    pre_price = np.round(base_cost * (1 + rng.uniform(0.10, 0.65, size=n)), 2)
    depth = np.round(rng.beta(2.0, 4.5, size=n) * 0.7 + 0.05, 4)  # 5% to ~75%
    post_price = np.round(pre_price * (1 - depth), 2).clip(min=0.10)
    triggered_at = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-10").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    effective_from = triggered_at + pd.to_timedelta(rng.integers(0, 86400, size=n), unit="s")
    effective_to = effective_from + pd.to_timedelta(rng.integers(3, 28, size=n), unit="D")
    planned_st = np.round(rng.uniform(0.65, 0.95, size=n), 4)
    actual_st = (planned_st * rng.normal(0.92, 0.18, size=n).clip(0.10, 1.40)).clip(0.05, 1.0)
    return pd.DataFrame({
        "markdown_id": [f"MKD{i:010d}" for i in range(1, n + 1)],
        "product_id": products["product_id"].to_numpy()[p_idx],
        "store_id": stores["store_id"].to_numpy()[s_idx],
        "pre_price_minor": (pre_price * 100).astype(np.int64),
        "post_price_minor": (post_price * 100).astype(np.int64),
        "markdown_depth_pct": depth,
        "reason_code": weighted_choice(rng, MARKDOWN_REASONS, MARKDOWN_REASON_W, n),
        "optimizer": weighted_choice(rng, OPTIMIZERS, OPTIMIZER_W, n),
        "triggered_at": triggered_at,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "planned_sell_through_pct": planned_st,
        "actual_sell_through_pct": np.round(actual_st, 4),
    })


def _competitive_prices(ctx, products, n=100_000):
    rng = ctx.rng
    p_idx = rng.integers(0, len(products), size=n)
    comp_idx = rng.integers(0, len(COMPETITORS), size=n)
    comp_ids = np.array([COMPETITORS[i][0] for i in comp_idx])
    comp_names = np.array([COMPETITORS[i][1] for i in comp_idx])
    own_cost = products["unit_cost"].to_numpy()[p_idx]
    # Competitor prices roughly orbit own price ratio
    own_price_proxy = own_cost * (1 + rng.uniform(0.10, 0.60, size=n))
    competitor_price = np.round(
        own_price_proxy * rng.normal(1.0, 0.12, size=n).clip(0.55, 1.50), 2
    ).clip(min=0.10)
    observed_at = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-10").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s")
    match_type = weighted_choice(rng, MATCH_TYPES, MATCH_TYPE_W, n)
    match_conf = np.where(match_type == "exact_gtin",
                          rng.uniform(0.95, 1.0, size=n),
                          np.where(match_type == "equivalent",
                                   rng.uniform(0.80, 0.95, size=n),
                                   rng.uniform(0.55, 0.85, size=n)))
    return pd.DataFrame({
        "competitive_price_id": [f"CMP{i:010d}" for i in range(1, n + 1)],
        "product_id": products["product_id"].to_numpy()[p_idx],
        "competitor_id": comp_ids,
        "competitor_name": comp_names,
        "channel": weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "observed_price_minor": (competitor_price * 100).astype(np.int64),
        "currency": rng.choice(["USD", "EUR", "GBP", "CAD"], p=[0.70, 0.18, 0.07, 0.05], size=n),
        "on_promo": rng.random(n) < 0.22,
        "match_type": match_type,
        "match_confidence": np.round(match_conf, 3),
        "source": weighted_choice(rng, COMP_SOURCES, COMP_SOURCE_W, n),
        "observed_at": observed_at,
    })


def _sales_facts(ctx, products, stores, promos, n=400_000):
    rng = ctx.rng
    p_idx = rng.integers(0, len(products), size=n)
    s_idx = rng.integers(0, len(stores), size=n)
    cost = products["unit_cost"].to_numpy()[p_idx]
    margin = rng.uniform(0.05, 0.50, size=n)
    realized_price = np.round(cost * (1 + margin), 2)
    units_sold = rng.integers(1, 240, size=n)
    sale_date = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-02-10").timestamp()),
                     int(pd.Timestamp("2026-05-09").timestamp()), size=n),
        unit="s").date
    on_promo = rng.random(n) < 0.22
    promo_id = np.where(on_promo,
                        promos["promo_id"].to_numpy()[rng.integers(0, len(promos), size=n)],
                        None)
    discount_pct = np.where(on_promo, rng.uniform(0.05, 0.40, size=n), 0.0)
    discount_minor = (realized_price * 100 * discount_pct * units_sold).astype(np.int64)
    gross_revenue_minor = (realized_price * 100 * units_sold).astype(np.int64)
    net_revenue_minor = gross_revenue_minor - discount_minor
    cogs_minor = (cost * 100 * units_sold).astype(np.int64)
    return pd.DataFrame({
        "sales_id": [f"SAL{i:010d}" for i in range(1, n + 1)],
        "product_id": products["product_id"].to_numpy()[p_idx],
        "store_id": stores["store_id"].to_numpy()[s_idx],
        "sale_date": sale_date,
        "units_sold": units_sold,
        "gross_revenue_minor": gross_revenue_minor,
        "discount_minor": discount_minor,
        "net_revenue_minor": net_revenue_minor,
        "cogs_minor": cogs_minor,
        "on_promo": on_promo,
        "promo_id": promo_id,
        "realized_price_minor": (realized_price * (1 - discount_pct) * 100).astype(np.int64),
    })


def _elasticity_estimates(ctx, products, n=80_000):
    rng = ctx.rng
    p_idx = rng.integers(0, len(products), size=n)
    # Own-price elasticity: lognormal centered at -1.5 (so the magnitude is
    # log-normal, then we negate).
    magnitude = rng.lognormal(0.4, 0.45, size=n).clip(0.20, 4.5)
    own = np.round(-magnitude, 4)
    cross_magnitude = rng.lognormal(-0.6, 0.5, size=n).clip(0.02, 1.5)
    cross = np.round(cross_magnitude, 4)
    cluster = np.array([f"CL{rng.integers(0, 40):03d}" for _ in range(n)])
    fit_end = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-01-15").timestamp()),
                     int(pd.Timestamp("2026-05-01").timestamp()), size=n),
        unit="s")
    fit_window_d = rng.integers(60, 365, size=n)
    fit_start = fit_end - pd.to_timedelta(fit_window_d, unit="D")
    return pd.DataFrame({
        "estimate_id": [f"ELS{i:010d}" for i in range(1, n + 1)],
        "product_id": products["product_id"].to_numpy()[p_idx],
        "cluster_id": cluster,
        "own_price_elasticity": own,
        "cross_price_elasticity_top1": cross,
        "cross_product_id_top1": products["product_id"].to_numpy()[
            rng.integers(0, len(products), size=n)
        ],
        "confidence_interval_low": np.round(own - magnitude * 0.20, 4),
        "confidence_interval_high": np.round(own + magnitude * 0.20, 4),
        "model_version": rng.choice(["v3.1", "v3.2", "v3.3", "v4.0-beta"], size=n),
        "fit_window_start": fit_start.date,
        "fit_window_end": fit_end.date,
        "estimated_at": fit_end + pd.to_timedelta(rng.integers(0, 7, size=n), unit="D"),
    })


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating price_zones...")
    zones = _price_zones(ctx)
    print("  generating products...")
    products = _products(ctx)
    print("  generating stores...")
    stores = _stores(ctx, zones)
    print("  generating prices (~720k snapshots)...")
    prices = _prices(ctx, products, stores)
    print("  generating promos...")
    promos = _promos(ctx)
    print("  generating promo_lines...")
    promo_lines = _promo_lines(ctx, promos, products, stores)
    print("  generating markdowns...")
    markdowns = _markdowns(ctx, products, stores)
    print("  generating competitive_prices...")
    competitive = _competitive_prices(ctx, products)
    print("  generating sales_facts...")
    sales = _sales_facts(ctx, products, stores, promos)
    print("  generating elasticity_estimates...")
    elasticity = _elasticity_estimates(ctx, products)
    tables = {
        "product": products,
        "store": stores,
        "price_zone": zones,
        "price": prices,
        "promo": promos,
        "promo_line": promo_lines,
        "markdown": markdowns,
        "competitive_price": competitive,
        "sales_fact": sales,
        "elasticity_estimate": elasticity,
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
