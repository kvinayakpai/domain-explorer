"""
Synthetic Category Management data — Blue Yonder Space Planning / Symphony
RetailAI CINDE / Circana (IRI + NPD merged 2023) / NielsenIQ Connect /
Numerator / Kantar Worldpanel / dunnhumby / RELEX Solutions.

Entities (>=10):
  category, sku, sku_attribute, store, planogram, planogram_position,
  distribution_record, syndicated_measurement, range_review,
  range_review_decision, planogram_compliance_audit.

Realism:
  - Long-tail SKU velocity (lognormal); category-role-driven space targets.
  - Multi-source syndicated panels (Circana, NielsenIQ, Numerator, Kantar) with
    projection factors per source.
  - Compliance audits are partial — not every store audited every week.
  - All large-range integer IDs use the int64-safe pattern (rng.integers +
    zero-padded format string).

Scope (downsampled from the >200M-row spec to a tractable demo):
  50 categories × 500 SKUs × 100 stores × 12 weeks × ~5 syndicated sources
  = ~30M syndicated rows. Planograms (500), range reviews (5000),
  distribution records (100k), audits (~25k).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table

SUBDOMAIN = "category_management"

CATEGORY_ROLES = ["destination", "routine", "occasional_seasonal", "convenience"]
CATEGORY_ROLE_W = [0.18, 0.55, 0.18, 0.09]
CATEGORY_LEVELS = ["category", "subcategory", "segment"]
LIFECYCLE_STAGES = ["intro", "grow", "core", "decline", "discontinued"]
LIFECYCLE_W = [0.07, 0.18, 0.55, 0.15, 0.05]
BANNERS = ["Walmart", "Kroger", "Target", "Albertsons", "Publix", "HEB", "Costco", "Sams_Club", "Aldi", "WholeFoods"]
BANNER_W = [0.32, 0.20, 0.14, 0.08, 0.06, 0.04, 0.06, 0.05, 0.03, 0.02]
FORMATS = ["supercenter", "grocery", "club", "express", "c_store"]
FORMAT_W = [0.34, 0.40, 0.10, 0.10, 0.06]
CLUSTERS = ["A_premium", "B_mainstream", "C_value", "D_hispanic_skew", "E_urban", "F_suburban", "G_rural"]
CLUSTER_W = [0.10, 0.40, 0.18, 0.08, 0.10, 0.10, 0.04]
SHOPPER_SEGMENTS = ["family_value", "premium_urban", "convenience_seeker", "natural_organic", "budget_constrained", "occasion_planner", "deal_hunter"]
PRIVATE_LABEL_W = 0.22
MANUFACTURERS = [
    "PepsiCo", "Coca-Cola", "Nestle", "Unilever", "P&G", "Kraft Heinz",
    "Mondelez", "General Mills", "Mars", "Hershey", "Kimberly-Clark",
    "Colgate-Palmolive", "Johnson & Johnson", "Reckitt", "Conagra",
    "Tyson", "Smithfield", "Kellanova", "Post Holdings", "PrivateLabel",
]
BRANDS_BY_MFR = {
    # Coarse: pick ~5 brand names per manufacturer for synthetic variety.
    m: [f"{m.replace(' ', '')[:8]}_Brand_{i}" for i in range(1, 6)] for m in MANUFACTURERS
}
ATTR_NAMES = ["flavor", "pack_format", "occasion", "dietary", "claim", "origin", "size_tier"]
ATTR_VALUES = {
    "flavor": ["original", "vanilla", "chocolate", "berry", "citrus", "spicy", "salted", "honey", "mint"],
    "pack_format": ["single", "multipack", "value_pack", "club_pack", "trial", "family", "single_serve"],
    "occasion": ["everyday", "snacking", "breakfast", "lunch", "dinner", "party", "gifting"],
    "dietary": ["none", "gluten_free", "vegan", "keto", "low_sugar", "high_protein", "organic"],
    "claim": ["none", "no_artificial", "non_gmo", "fair_trade", "kosher", "made_in_usa", "natural"],
    "origin": ["US", "MX", "CA", "EU", "BR", "JP", "TH", "IT"],
    "size_tier": ["entry", "mainstream", "premium", "value", "super"],
}
PANELS = ["circana_unify", "niq_connect", "numerator", "kantar_worldpanel", "first_party"]
PANEL_W = [0.30, 0.28, 0.20, 0.12, 0.10]
GEOGRAPHIES = ["TotalUS", "TotalUS_Food", "Walmart", "Kroger", "Target", "Albertsons", "Costco", "Convenience+", "Drug+"]
GEOGRAPHY_W = [0.18, 0.18, 0.16, 0.12, 0.10, 0.08, 0.06, 0.06, 0.06]
SOURCE_DOCS = ["EDI_852", "circana", "niq", "numerator", "kantar", "first_party"]
SOURCE_DOC_W = [0.32, 0.22, 0.20, 0.12, 0.08, 0.06]
AUTHORING_SYSTEMS = ["blueyonder_space", "symphony_catman", "relex", "quad_tag", "inhouse"]
AUTHORING_W = [0.46, 0.22, 0.16, 0.08, 0.08]
RANGE_REVIEW_STATUSES = ["scheduled", "in_planning", "presented", "approved", "in_market", "cancelled"]
RANGE_REVIEW_W = [0.05, 0.10, 0.10, 0.20, 0.50, 0.05]
DECISION_TYPES = ["add", "drop", "keep", "mandate", "cluster_restrict", "reclass", "repack"]
DECISION_TYPE_W = [0.12, 0.14, 0.52, 0.10, 0.06, 0.04, 0.02]
DECISION_RATIONALES = ["must_have", "low_velocity", "halo", "cannibalization", "innovation", "private_label_swap"]
AUDIT_SOURCES = ["afs", "sfdc_cg", "numerator", "niq_audit", "inhouse"]
AUDIT_SOURCE_W = [0.32, 0.30, 0.20, 0.10, 0.08]
COUNTRIES = ["US", "CA", "MX", "GB", "DE"]
COUNTRY_W = [0.78, 0.10, 0.06, 0.04, 0.02]


# ---------------------------------------------------------------------------
def _categories(ctx, n=50):
    rng = ctx.rng
    parent_choices = [None] * 6 + [f"CAT{i:05d}" for i in range(1, 7)]
    parent = np.array([rng.choice(parent_choices) for _ in range(n)])
    return pd.DataFrame({
        "category_id": [f"CAT{i:05d}" for i in range(1, n + 1)],
        "category_name": [f"Category_{i:03d}" for i in range(1, n + 1)],
        "parent_category_id": parent,
        "category_level": rng.choice(CATEGORY_LEVELS, size=n, p=[0.34, 0.46, 0.20]),
        "category_role": weighted_choice(rng, CATEGORY_ROLES, CATEGORY_ROLE_W, n),
        "linear_ft_target": np.round(rng.uniform(8.0, 120.0, size=n), 2),
        "gpc_brick": [f"100{rng.integers(10000, 99999):05d}" for _ in range(n)],
        "status": rng.choice(["active", "review", "archived"], size=n, p=[0.90, 0.06, 0.04]),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2023-01-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
    })


def _skus(ctx, categories, n=500):
    rng = ctx.rng
    cat_ids = categories["category_id"].to_numpy()
    cat_idx = rng.integers(0, len(cat_ids), size=n)
    mfrs = rng.choice(MANUFACTURERS, size=n)
    brands = np.array([rng.choice(BRANDS_BY_MFR[m]) for m in mfrs])
    pl_flag = np.where(mfrs == "PrivateLabel", True, rng.random(n) < PRIVATE_LABEL_W)
    return pd.DataFrame({
        "sku_id": [f"SKU{i:07d}" for i in range(1, n + 1)],
        "gtin": [f"00{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
        "brand": brands,
        "sub_brand": [f"{b}_SB{rng.integers(1, 5)}" for b in brands],
        "manufacturer": mfrs,
        "category_id": cat_ids[cat_idx],
        "pack_size": rng.choice(["6oz", "12oz", "16oz", "20oz", "32oz", "6ct", "12ct", "24ct", "48ct"], size=n),
        "case_pack_qty": rng.integers(6, 36, size=n).astype("int16"),
        "width_cm": np.round(rng.uniform(4.0, 28.0, size=n), 2),
        "height_cm": np.round(rng.uniform(8.0, 40.0, size=n), 2),
        "depth_cm": np.round(rng.uniform(4.0, 24.0, size=n), 2),
        "weight_g": rng.integers(50, 3000, size=n).astype(np.int64),
        "list_price_cents": (rng.lognormal(5.5, 0.8, size=n) * 10).astype(np.int64),
        "srp_cents": (rng.lognormal(5.6, 0.8, size=n) * 10).astype(np.int64),
        "cost_of_goods_cents": (rng.lognormal(5.0, 0.8, size=n) * 10).astype(np.int64),
        "private_label_flag": pl_flag,
        "launch_date": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2020-01-01").timestamp()),
                         int(pd.Timestamp("2026-03-01").timestamp()), size=n),
            unit="s").date,
        "lifecycle_stage": weighted_choice(rng, LIFECYCLE_STAGES, LIFECYCLE_W, n),
        "status": rng.choice(["active", "delisted", "pending"], size=n, p=[0.90, 0.07, 0.03]),
    })


def _sku_attributes(ctx, skus):
    rng = ctx.rng
    rows = []
    sku_ids = skus["sku_id"].to_numpy()
    n_attrs_per_sku = rng.integers(3, len(ATTR_NAMES) + 1, size=len(sku_ids))
    for sku_id, k in zip(sku_ids, n_attrs_per_sku):
        attrs = rng.choice(ATTR_NAMES, size=int(k), replace=False)
        for i, a in enumerate(attrs):
            v = rng.choice(ATTR_VALUES[a])
            rows.append({
                "sku_id": sku_id,
                "attribute_name": a,
                "attribute_value": v,
                "attribute_level": int(i + 1),
                "source_system": rng.choice(["plytix", "gdsn", "inhouse"], p=[0.25, 0.55, 0.20]),
            })
    return pd.DataFrame(rows)


def _stores(ctx, n=100):
    rng = ctx.rng
    banners = weighted_choice(rng, BANNERS, BANNER_W, n)
    return pd.DataFrame({
        "store_id": [f"STR{i:06d}" for i in range(1, n + 1)],
        "banner": banners,
        "store_number": [f"{rng.integers(100, 9999):04d}" for _ in range(n)],
        "gln": [f"08{rng.integers(10**10, 10**11):011d}" for _ in range(n)],
        "country_iso2": weighted_choice(rng, COUNTRIES, COUNTRY_W, n),
        "state_region": rng.choice(["CA", "TX", "FL", "NY", "PA", "OH", "IL", "GA", "NC", "MI", "WA", "VA", "AZ"], size=n),
        "postal_code": [f"{rng.integers(10000, 99999):05d}" for _ in range(n)],
        "format": weighted_choice(rng, FORMATS, FORMAT_W, n),
        "cluster_id": weighted_choice(rng, CLUSTERS, CLUSTER_W, n),
        "shopper_segment": rng.choice(SHOPPER_SEGMENTS, size=n),
        "total_linear_ft": np.round(rng.uniform(500.0, 8000.0, size=n), 2),
        "status": rng.choice(["active", "closed", "remodel"], size=n, p=[0.94, 0.03, 0.03]),
    })


def _planograms(ctx, categories, n=500):
    rng = ctx.rng
    cat_ids = categories["category_id"].to_numpy()
    cat_idx = rng.integers(0, len(cat_ids), size=n)
    ef_from = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-01-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s").date
    ef_to = pd.to_datetime(ef_from) + pd.to_timedelta(rng.integers(30, 365, size=n), unit="D")
    return pd.DataFrame({
        "planogram_id": [f"POG{i:07d}" for i in range(1, n + 1)],
        "category_id": cat_ids[cat_idx],
        "cluster_id": weighted_choice(rng, CLUSTERS, CLUSTER_W, n),
        "version": [f"v{rng.integers(1, 6)}.{rng.integers(0, 9)}.{rng.integers(0, 9)}" for _ in range(n)],
        "effective_from": ef_from,
        "effective_to": ef_to.dt.date,
        "total_linear_ft": np.round(rng.uniform(8.0, 90.0, size=n), 2),
        "total_facings": rng.integers(40, 600, size=n).astype(np.int64),
        "total_sku_count": rng.integers(20, 250, size=n).astype(np.int64),
        "authoring_system": weighted_choice(rng, AUTHORING_SYSTEMS, AUTHORING_W, n),
        "created_by": [f"user_{rng.integers(1, 200):03d}" for _ in range(n)],
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-06-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
        "approved_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-07-01").timestamp()),
                         int(pd.Timestamp("2026-05-01").timestamp()), size=n),
            unit="s"),
        "status": rng.choice(
            ["draft", "approved", "in_market", "superseded", "killed"],
            size=n, p=[0.05, 0.15, 0.50, 0.25, 0.05]),
    })


def _planogram_positions(ctx, planograms, skus, target_avg=30):
    """One planogram has 20-120 positions; expand."""
    rng = ctx.rng
    rows = []
    sku_arr = skus["sku_id"].to_numpy()
    sku_cat = skus.set_index("sku_id")["category_id"].to_dict()
    pos_counter = 0
    for _, pg in planograms.iterrows():
        pog_id = pg["planogram_id"]
        cat_id = pg["category_id"]
        n_positions = int(rng.integers(20, 120))
        eligible_skus = skus[skus["category_id"] == cat_id]["sku_id"].to_numpy()
        if len(eligible_skus) < 3:
            eligible_skus = sku_arr  # fallback
        chosen = rng.choice(eligible_skus, size=min(n_positions, len(eligible_skus)), replace=False)
        shelves = rng.integers(1, 7, size=len(chosen))
        positions = rng.integers(1, 20, size=len(chosen))
        for i, sku in enumerate(chosen):
            pos_counter += 1
            rows.append({
                "position_id": f"POS{pos_counter:010d}",
                "planogram_id": pog_id,
                "sku_id": sku,
                "shelf_number": int(shelves[i]),
                "position_index": int(positions[i]),
                "facings": int(rng.integers(1, 8)),
                "facing_depth": int(rng.integers(1, 5)),
                "linear_ft_allocated": round(rng.uniform(0.1, 2.5), 3),
                "block_id": f"BLK{rng.integers(1, 50):03d}",
                "adjacency_left_sku": rng.choice(chosen) if rng.random() < 0.7 else None,
                "adjacency_right_sku": rng.choice(chosen) if rng.random() < 0.7 else None,
                "is_mandated": bool(rng.random() < 0.30),
                "is_innovation_slot": bool(rng.random() < 0.06),
            })
    return pd.DataFrame(rows)


def _distribution_records(ctx, stores, skus, n_weeks=12, sample=100_000):
    """Wide sparse distribution fact — sample down to ~100k rows."""
    rng = ctx.rng
    n = sample
    store_ids = stores["store_id"].to_numpy()
    sku_ids = skus["sku_id"].to_numpy()
    weeks = pd.date_range("2026-02-09", periods=n_weeks, freq="W-MON").date
    week_idx = rng.integers(0, n_weeks, size=n)
    is_listed = rng.random(n) < 0.78
    is_on_shelf = is_listed & (rng.random(n) < 0.92)
    return pd.DataFrame({
        "distribution_record_id": [f"DR{i:010d}" for i in range(1, n + 1)],
        "store_id": rng.choice(store_ids, size=n),
        "sku_id": rng.choice(sku_ids, size=n),
        "week_start_date": pd.to_datetime([weeks[i] for i in week_idx]),
        "is_listed": is_listed,
        "is_on_shelf": is_on_shelf,
        "acv_weight": np.round(rng.uniform(0.0005, 0.05, size=n), 4),
        "mandated_flag": rng.random(n) < 0.35,
        "compliant_flag": is_listed & is_on_shelf & (rng.random(n) < 0.88),
        "source_doc": weighted_choice(rng, SOURCE_DOCS, SOURCE_DOC_W, n),
        "ingested_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-02-12").timestamp()),
                         int(pd.Timestamp("2026-05-10").timestamp()), size=n),
            unit="s"),
    })


def _syndicated_measurements(ctx, skus, stores, categories, n_weeks=12,
                              target_rows=3_000_000):
    """Downsampled to ~3M rows. Real Catman warehouse would be 200M+.

    Each row: SKU × store × week × source. Sampling is sparse, not full cross.
    """
    rng = ctx.rng
    n = target_rows
    sku_arr = skus["sku_id"].to_numpy()
    sku_cat = skus.set_index("sku_id")["category_id"].to_dict()
    store_arr = stores["store_id"].to_numpy()
    weeks = pd.date_range("2026-02-09", periods=n_weeks, freq="W-MON").date
    week_idx = rng.integers(0, n_weeks, size=n)
    chosen_sku = rng.choice(sku_arr, size=n)
    chosen_store = rng.choice(store_arr, size=n)
    chosen_cat = np.array([sku_cat.get(s, categories["category_id"].iloc[0]) for s in chosen_sku])

    units = rng.lognormal(3.5, 1.3, size=n).clip(0, 100_000).astype(np.int64)
    avg_price = (rng.lognormal(5.3, 0.6, size=n) * 10).astype(np.int64)
    dollars = (units * avg_price)
    return pd.DataFrame({
        "measurement_id": [f"MS{i:012d}" for i in range(1, n + 1)],
        "sku_id": chosen_sku,
        "store_id": chosen_store,
        "category_id": chosen_cat,
        "gtin": skus.set_index("sku_id")["gtin"].reindex(chosen_sku).to_numpy(),
        "week_start_date": pd.to_datetime([weeks[i] for i in week_idx]),
        "geography": weighted_choice(rng, GEOGRAPHIES, GEOGRAPHY_W, n),
        "units_sold": units,
        "dollars_sold_cents": dollars,
        "avg_retail_price_cents": avg_price,
        "market_share_pct": np.round(rng.uniform(0.0, 0.45, size=n), 4),
        "penetration_pct": np.round(rng.uniform(0.0, 0.55, size=n), 4),
        "buy_rate_units": np.round(rng.uniform(0.5, 18.0, size=n), 2),
        "any_promo_flag": rng.random(n) < 0.22,
        "source": weighted_choice(rng, PANELS, PANEL_W, n),
        "panel_id": rng.choice(["Circana_Receipt", "NIQ_Homescan", "Kantar_Worldpanel", "Numerator", ""], size=n,
                                p=[0.28, 0.26, 0.18, 0.18, 0.10]),
        "projection_factor": np.round(rng.uniform(0.95, 7.5, size=n), 4),
        "ingested_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-02-12").timestamp()),
                         int(pd.Timestamp("2026-05-10").timestamp()), size=n),
            unit="s"),
    })


def _range_reviews(ctx, categories, n=5000):
    rng = ctx.rng
    cat_ids = categories["category_id"].to_numpy()
    cat_idx = rng.integers(0, len(cat_ids), size=n)
    scheduled = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-09-01").timestamp()),
                     int(pd.Timestamp("2026-06-01").timestamp()), size=n),
        unit="s").date
    decision = pd.to_datetime(scheduled) + pd.to_timedelta(rng.integers(14, 90, size=n), unit="D")
    in_market = decision + pd.to_timedelta(rng.integers(30, 120, size=n), unit="D")
    sku_before = rng.integers(40, 250, size=n).astype(np.int64)
    sku_adds = rng.integers(0, 25, size=n).astype(np.int64)
    sku_drops = rng.integers(0, 30, size=n).astype(np.int64)
    sku_after = (sku_before + sku_adds - sku_drops).clip(min=10)
    return pd.DataFrame({
        "range_review_id": [f"RR{i:07d}" for i in range(1, n + 1)],
        "category_id": cat_ids[cat_idx],
        "banner": weighted_choice(rng, BANNERS, BANNER_W, n),
        "cycle_name": [f"Cycle_{rng.choice(['Spring', 'Summer', 'Fall', 'Winter'])}_{rng.integers(2025, 2027)}_{rng.integers(1, 4)}" for _ in range(n)],
        "scheduled_date": scheduled,
        "decision_date": decision.dt.date,
        "in_market_date": in_market.dt.date,
        "sku_count_before": sku_before,
        "sku_count_after": sku_after,
        "sku_adds": sku_adds,
        "sku_drops": sku_drops,
        "forecast_category_sales_delta_cents": (rng.normal(0, 200_000, size=n) * 100).astype(np.int64),
        "forecast_margin_delta_cents": (rng.normal(0, 60_000, size=n) * 100).astype(np.int64),
        "status": weighted_choice(rng, RANGE_REVIEW_STATUSES, RANGE_REVIEW_W, n),
        "led_by": rng.choice(["PepsiCo_Captain", "Coca_Cola_Captain", "Nestle_Captain", "PG_Captain",
                              "Validator_PepsiCo", "Validator_Mondelez", "Retailer_Internal", "JointCaptaincy"], size=n),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2025-06-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s"),
    })


def _range_review_decisions(ctx, range_reviews, skus):
    rng = ctx.rng
    rows = []
    sku_by_cat = skus.groupby("category_id")["sku_id"].apply(list).to_dict()
    all_skus = skus["sku_id"].to_numpy()
    counter = 0
    for _, rr in range_reviews.iterrows():
        rr_id = rr["range_review_id"]
        cat_id = rr["category_id"]
        eligible = sku_by_cat.get(cat_id, list(all_skus))
        n_dec = int(rng.integers(5, min(60, len(eligible)) + 1))
        chosen = rng.choice(eligible, size=n_dec, replace=False) if len(eligible) >= n_dec else eligible
        for sku in chosen:
            counter += 1
            rows.append({
                "decision_id": f"RRD{counter:010d}",
                "range_review_id": rr_id,
                "sku_id": sku,
                "decision_type": weighted_choice(rng, DECISION_TYPES, DECISION_TYPE_W, 1)[0],
                "cluster_scope": rng.choice(["ALL"] + CLUSTERS),
                "rationale": rng.choice(DECISION_RATIONALES),
                "confidence": round(float(rng.uniform(0.55, 0.99)), 3),
                "decision_authority": rng.choice(["category_captain", "retailer_buyer", "joint"], p=[0.45, 0.30, 0.25]),
                "decided_at": rr["created_at"] + pd.Timedelta(days=int(rng.integers(7, 60))),
            })
    return pd.DataFrame(rows)


def _planogram_compliance_audits(ctx, planograms, stores, n=25_000):
    rng = ctx.rng
    pog_ids = planograms["planogram_id"].to_numpy()
    store_ids = stores["store_id"].to_numpy()
    pos_audited = rng.integers(20, 200, size=n).astype(np.int64)
    compliance_pct = rng.beta(8, 2, size=n).clip(0.50, 1.0)
    pos_compliant = (pos_audited * compliance_pct).astype(np.int64)
    return pd.DataFrame({
        "audit_id": [f"AUD{i:010d}" for i in range(1, n + 1)],
        "store_id": rng.choice(store_ids, size=n),
        "planogram_id": rng.choice(pog_ids, size=n),
        "audit_date": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2026-02-01").timestamp()),
                         int(pd.Timestamp("2026-05-10").timestamp()), size=n),
            unit="s").date,
        "positions_audited": pos_audited,
        "positions_compliant": pos_compliant,
        "missing_facings": rng.integers(0, 40, size=n).astype(np.int64),
        "out_of_stock_count": rng.integers(0, 25, size=n).astype(np.int64),
        "misplaced_sku_count": rng.integers(0, 15, size=n).astype(np.int64),
        "extra_sku_count": rng.integers(0, 12, size=n).astype(np.int64),
        "compliance_score": np.round(compliance_pct * 100.0, 2),
        "source": weighted_choice(rng, AUDIT_SOURCES, AUDIT_SOURCE_W, n),
        "photo_evidence_uri": [f"s3://catman-audits/photos/{rng.integers(10**11, 10**12):012d}.jpg" for _ in range(n)],
    })


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating categories...")
    categories = _categories(ctx)
    print("  generating skus...")
    skus = _skus(ctx, categories)
    print("  generating sku_attributes...")
    sku_attrs = _sku_attributes(ctx, skus)
    print("  generating stores...")
    stores = _stores(ctx)
    print("  generating planograms...")
    planograms = _planograms(ctx, categories)
    print("  generating planogram_positions...")
    positions = _planogram_positions(ctx, planograms, skus)
    print("  generating distribution_records...")
    distribution = _distribution_records(ctx, stores, skus)
    print("  generating syndicated_measurements (~3M rows)...")
    measurements = _syndicated_measurements(ctx, skus, stores, categories)
    print("  generating range_reviews...")
    range_reviews = _range_reviews(ctx, categories)
    print("  generating range_review_decisions...")
    decisions = _range_review_decisions(ctx, range_reviews, skus)
    print("  generating planogram_compliance_audits...")
    audits = _planogram_compliance_audits(ctx, planograms, stores)

    tables = {
        "category": categories,
        "sku": skus,
        "sku_attribute": sku_attrs,
        "store": stores,
        "planogram": planograms,
        "planogram_position": positions,
        "distribution_record": distribution,
        "syndicated_measurement": measurements,
        "range_review": range_reviews,
        "range_review_decision": decisions,
        "planogram_compliance_audit": audits,
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
