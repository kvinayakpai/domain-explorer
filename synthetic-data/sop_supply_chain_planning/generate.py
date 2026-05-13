"""
Synthetic S&OP / IBP (Integrated Business Planning) data.

Vendor backdrop:
  SAP IBP, Kinaxis RapidResponse, o9 Solutions, Blue Yonder SCP, Oracle SCP
  Cloud, Anaplan, Logility, ToolsGroup SO99+, Demand Solutions, John Galt
  Solutions, GAINSystems, Steelwedge legacy.
  Standards: ASCM/APICS SCOR, ASCM IBP (Oliver Wight 5-step), GS1 GTIN/GLN,
  ISO 28000, EDI 852/830/862.

Entities (>=10):
  item, location, customer, sop_cycle, sales_history, forecast, supply_plan,
  inventory_position, capacity, scenario, bom.

Scale (downsampled from full ambition):
  1,000 items × 20 locations × 26 weeks × 3 forecast versions ≈ 1.56M forecast rows.
  ~100k supply plans, ~200k inventory positions, 50 capacity profiles, 10 scenarios.

Realism:
  - Lognormal demand by item-family with ABC/XYZ stratification.
  - Forecast versions (statistical_baseline → consensus) with realistic bias
    and MAPE per stage (baseline ~28% MAPE, consensus ~18%).
  - DOH targeting by ABC class, with occasional stockouts and excess
    inventory across the tail.
  - Capacity utilization ~78% mean with a long upper tail (bottlenecks).
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

SUBDOMAIN = "sop_supply_chain_planning"

# --- enumeration vocabularies ------------------------------------------------
ITEM_CLASSES = ["A", "B", "C"]
ITEM_CLASS_W = [0.20, 0.30, 0.50]                   # Pareto-ish
XYZ_CLASSES = ["X", "Y", "Z"]
XYZ_CLASS_W = [0.45, 0.35, 0.20]
LIFECYCLE = ["intro", "growth", "mature", "decline", "eol"]
LIFECYCLE_W = [0.06, 0.16, 0.58, 0.16, 0.04]
FAMILIES = [
    "BEV-CARBONATED", "BEV-WATER", "BEV-JUICE", "SNK-SALTY", "SNK-SWEET",
    "DAIRY-MILK", "DAIRY-YOGURT", "BAKERY-BREAD", "FROZEN-MEAL", "FROZEN-DESSERT",
    "PERSONAL-CARE", "HOME-CLEAN", "PETFOOD-DRY", "PETFOOD-WET",
    "AUTO-PARTS-FILTER", "AUTO-PARTS-BRAKE", "OTC-ANALGESIC", "OTC-COLD",
    "ELECTRO-AUDIO", "ELECTRO-WEARABLE",
]
UOM = ["EA", "CS", "KG", "L"]
UOM_W = [0.55, 0.30, 0.10, 0.05]
ITEM_STATUS = ["active", "phasing_in", "phasing_out", "obsolete"]
ITEM_STATUS_W = [0.86, 0.04, 0.06, 0.04]

LOCATION_TYPES = ["plant", "dc", "warehouse", "supplier", "customer_dc"]
LOCATION_TYPE_W = [0.10, 0.30, 0.20, 0.30, 0.10]
REGIONS = ["NA", "EMEA", "APAC", "LATAM"]
REGION_W = [0.42, 0.30, 0.18, 0.10]
COUNTRIES = ["US", "MX", "CA", "GB", "DE", "FR", "IT", "ES", "NL", "PL",
             "JP", "KR", "SG", "AU", "IN", "CN", "BR", "AR"]

CHANNELS = ["retail", "ecom", "distributor", "direct", "ota", "other"]
CHANNEL_W = [0.42, 0.18, 0.20, 0.10, 0.06, 0.04]
SEGMENTS = ["strategic", "key", "growth", "tail"]
SEGMENT_W = [0.08, 0.20, 0.32, 0.40]

FORECAST_VERSIONS = ["statistical_baseline", "sales_input", "consensus"]
FV_W = [0.40, 0.25, 0.35]
PERIOD_GRAINS = ["week", "month"]
PERIOD_GRAIN_W = [0.70, 0.30]

SUPPLY_TYPES = ["produce", "transfer", "purchase", "co_manufacture", "alternate"]
SUPPLY_TYPE_W = [0.42, 0.22, 0.24, 0.08, 0.04]
SUPPLY_STATUS = ["draft", "firm", "released", "cancelled"]
SUPPLY_STATUS_W = [0.18, 0.32, 0.45, 0.05]

SCENARIO_TYPES = ["base", "upside", "downside", "disruption", "capacity_invest",
                  "tariff", "new_product", "eol"]
SCENARIO_TYPE_W = [0.20, 0.16, 0.16, 0.12, 0.10, 0.10, 0.10, 0.06]
SCENARIO_STATUS = ["draft", "evaluated", "adopted", "rejected", "archived"]
SCENARIO_STATUS_W = [0.12, 0.36, 0.18, 0.20, 0.14]

RESOURCE_TYPES = ["line", "machine", "labor", "supplier", "tooling"]
RESOURCE_TYPE_W = [0.42, 0.30, 0.16, 0.08, 0.04]
CAP_STATUS = ["available", "reduced", "down", "qualified_alt"]
CAP_STATUS_W = [0.78, 0.10, 0.03, 0.09]

CYCLE_IDS = [f"2026-{m:02d}" for m in range(1, 7)]    # 2026-01 .. 2026-06

SOURCE_SYSTEMS_ACTUALS = ["ERP", "POS", "EDI_852", "syndicated"]
SOURCE_SYSTEMS_W = [0.60, 0.18, 0.14, 0.08]
MODEL_IDS = [
    "arima-pmdarima", "ets-statsforecast", "prophet", "lightgbm",
    "transformer-tide", "croston-tsb", "naive-seasonal", "demand-sense-blend",
]
MODEL_W = [0.16, 0.18, 0.12, 0.20, 0.10, 0.08, 0.06, 0.10]


# ---------------------------------------------------------------------------
def _items(ctx, n=1_000):
    rng = ctx.rng
    item_family = rng.choice(FAMILIES, size=n)
    item_class = weighted_choice(rng, ITEM_CLASSES, ITEM_CLASS_W, n)
    base_cost = np.where(
        item_class == "A", rng.lognormal(2.6, 0.6, size=n),
        np.where(item_class == "B", rng.lognormal(2.0, 0.6, size=n),
                 rng.lognormal(1.4, 0.5, size=n)),
    )
    return pd.DataFrame({
        "item_id": [f"ITM{i:07d}" for i in range(1, n + 1)],
        "gtin": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "sku": [f"SKU-{rng.integers(10**5, 10**6):06d}" for _ in range(n)],
        "item_family": item_family,
        "item_class": item_class,
        "xyz_class": weighted_choice(rng, XYZ_CLASSES, XYZ_CLASS_W, n),
        "lifecycle_stage": weighted_choice(rng, LIFECYCLE, LIFECYCLE_W, n),
        "uom_base": weighted_choice(rng, UOM, UOM_W, n),
        "planning_uom": weighted_choice(rng, UOM, UOM_W, n),
        "unit_cost": np.round(base_cost, 4),
        "unit_price": np.round(base_cost * rng.uniform(1.20, 2.40, size=n), 4),
        "shelf_life_days": rng.integers(30, 730, size=n).astype(int),
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2018-01-01").timestamp()),
                         int(pd.Timestamp("2025-12-31").timestamp()), size=n),
            unit="s"),
        "status": weighted_choice(rng, ITEM_STATUS, ITEM_STATUS_W, n),
    })


def _locations(ctx, n=20):
    rng = ctx.rng
    loc_type = weighted_choice(rng, LOCATION_TYPES, LOCATION_TYPE_W, n)
    tier = np.where(loc_type == "plant", 0,
            np.where(loc_type == "dc", 1,
            np.where(loc_type == "warehouse", 2,
            np.where(loc_type == "supplier", 0, 3)))).astype(int)
    return pd.DataFrame({
        "location_id": [f"LOC{i:04d}" for i in range(1, n + 1)],
        "gln": [f"{rng.integers(10**12, 10**13):013d}" for _ in range(n)],
        "location_type": loc_type,
        "country_iso2": rng.choice(COUNTRIES, size=n),
        "region": weighted_choice(rng, REGIONS, REGION_W, n),
        "tier": tier.astype(np.int16),
        "time_zone": rng.choice(
            ["UTC", "America/New_York", "America/Chicago", "America/Los_Angeles",
             "Europe/London", "Europe/Berlin", "Asia/Tokyo", "Asia/Singapore",
             "Australia/Sydney", "America/Sao_Paulo"], size=n),
        "status": rng.choice(["active", "active", "active", "active", "decommissioned"], size=n),
    })


def _customers(ctx, n=200):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "customer_id": [f"CUS{i:05d}" for i in range(1, n + 1)],
        "customer_name": [f.company() for _ in range(n)],
        "channel": weighted_choice(rng, CHANNELS, CHANNEL_W, n),
        "segment": weighted_choice(rng, SEGMENTS, SEGMENT_W, n),
        "country_iso2": rng.choice(COUNTRIES, size=n),
        "region": weighted_choice(rng, REGIONS, REGION_W, n),
        "priority": rng.integers(1, 6, size=n).astype(np.int16),
        "status": rng.choice(["active", "active", "active", "inactive"], size=n),
    })


def _sop_cycles(ctx):
    rng = ctx.rng
    n = len(CYCLE_IDS)
    cycle_starts = pd.to_datetime([f"{c}-01" for c in CYCLE_IDS])
    cycle_ends = cycle_starts + pd.DateOffset(months=1) - pd.Timedelta(days=1)
    return pd.DataFrame({
        "cycle_id": CYCLE_IDS,
        "cycle_start": cycle_starts,
        "cycle_end": cycle_ends,
        "product_review_ts": cycle_starts + pd.Timedelta(days=2),
        "demand_review_ts": cycle_starts + pd.Timedelta(days=7),
        "supply_review_ts": cycle_starts + pd.Timedelta(days=14),
        "integrated_reconciliation_ts": cycle_starts + pd.Timedelta(days=20),
        "mbr_ts": cycle_starts + pd.Timedelta(days=24),
        "signed_off_by": rng.choice(["A. Patel (COO)", "M. Chen (CSCO)", "R. Diaz (VP Plan)"], size=n),
        "signed_off_at": cycle_starts + pd.Timedelta(days=25),
        "status": ["signed_off"] * (n - 1) + ["open"],
    })


def _sales_history(ctx, items, locations, customers, n=300_000):
    rng = ctx.rng
    it_idx = rng.integers(0, len(items), size=n)
    lc_idx = rng.integers(0, len(locations), size=n)
    cu_idx = rng.integers(0, len(customers), size=n)
    # ~26 historical weeks ending today's window
    week_offsets = rng.integers(0, 52, size=n)
    period_start = pd.to_datetime("2025-05-04") + pd.to_timedelta(week_offsets * 7, unit="D")
    base_units = (rng.lognormal(3.4, 1.3, size=n)).astype(np.float64)
    item_class_mult = np.where(items["item_class"].to_numpy()[it_idx] == "A", 4.0,
                       np.where(items["item_class"].to_numpy()[it_idx] == "B", 1.6, 0.6))
    units = np.round(base_units * item_class_mult, 4)
    unit_price = items["unit_price"].to_numpy()[it_idx]
    return pd.DataFrame({
        "sales_history_id": np.arange(1, n + 1, dtype=np.int64),
        "item_id": items["item_id"].to_numpy()[it_idx],
        "location_id": locations["location_id"].to_numpy()[lc_idx],
        "customer_id": customers["customer_id"].to_numpy()[cu_idx],
        "period_start": period_start,
        "period_grain": "week",
        "shipped_units": units,
        "shipped_value": np.round(units * unit_price, 4),
        "returns_units": np.round(units * rng.uniform(0.0, 0.04, size=n), 4),
        "source_system": weighted_choice(rng, SOURCE_SYSTEMS_ACTUALS, SOURCE_SYSTEMS_W, n),
        "ingested_at": pd.Timestamp("2026-05-01"),
    })


def _forecasts(ctx, items, locations, customers, sop_cycles,
               n_items=1_000, n_locs=20, n_weeks=26, versions=None):
    """1k × 20 × 26 × 3 = 1.56M forecast rows."""
    rng = ctx.rng
    if versions is None:
        versions = FORECAST_VERSIONS
    cycle_id = sop_cycles["cycle_id"].iloc[-1]                 # latest cycle
    week_starts = pd.date_range("2026-05-04", periods=n_weeks, freq="7D")
    # Sample subset of customers to reduce explosion
    cust_sample = customers.sample(n=min(40, len(customers)), random_state=ctx.seed).reset_index(drop=True)

    # Use top-N items / locs to keep volume manageable
    item_sub = items.head(n_items).reset_index(drop=True)
    loc_sub = locations.head(n_locs).reset_index(drop=True)

    n = n_items * n_locs * n_weeks * len(versions)
    print(f"    materializing {n:,} forecast rows...")
    # Vectorize via mesh
    items_arr = np.tile(np.repeat(item_sub["item_id"].to_numpy(), n_locs * n_weeks * len(versions)), 1)
    locs_arr = np.tile(np.repeat(loc_sub["location_id"].to_numpy(), n_weeks * len(versions)), n_items)
    weeks_arr = np.tile(np.repeat(week_starts.to_numpy(), len(versions)), n_items * n_locs)
    versions_arr = np.tile(versions, n_items * n_locs * n_weeks)

    # Random customer per row
    cust_arr = cust_sample["customer_id"].to_numpy()[rng.integers(0, len(cust_sample), size=n)]

    # Demand base by item ABC mult
    item_class_lookup = dict(zip(item_sub["item_id"], item_sub["item_class"]))
    item_classes = np.array([item_class_lookup[i] for i in items_arr])
    base_units = rng.lognormal(2.8, 1.0, size=n) * np.where(
        item_classes == "A", 4.0, np.where(item_classes == "B", 1.6, 0.6))

    # Add seasonal week effect
    week_idx = (weeks_arr.astype("datetime64[D]").astype(int) % n_weeks)
    seasonal = 1.0 + 0.25 * np.sin(2 * np.pi * week_idx / 52)
    base_units *= seasonal

    # Stage-aware bias and noise per forecast_version
    bias = np.where(versions_arr == "statistical_baseline", rng.normal(1.06, 0.18, size=n),
            np.where(versions_arr == "sales_input",       rng.normal(1.12, 0.20, size=n),
                                                          rng.normal(1.01, 0.10, size=n)))
    forecast_units = np.round(base_units * bias, 4)

    # Unit price from item table
    unit_price_lookup = dict(zip(item_sub["item_id"], item_sub["unit_price"]))
    unit_prices = np.array([unit_price_lookup[i] for i in items_arr])
    forecast_value = np.round(forecast_units * unit_prices, 4)

    forecast_low = np.round(forecast_units * 0.85, 4)
    forecast_high = np.round(forecast_units * 1.18, 4)

    published_at = pd.Timestamp(f"{cycle_id}-15")
    locked = (versions_arr == "consensus")

    return pd.DataFrame({
        "forecast_id": np.arange(1, n + 1, dtype=np.int64),
        "item_id": items_arr,
        "location_id": locs_arr,
        "customer_id": cust_arr,
        "forecast_version": versions_arr,
        "cycle_id": cycle_id,
        "period_start": weeks_arr,
        "period_grain": "week",
        "forecast_units": forecast_units,
        "forecast_value": forecast_value,
        "forecast_low": forecast_low,
        "forecast_high": forecast_high,
        "model_id": rng.choice(MODEL_IDS, p=MODEL_W, size=n),
        "published_at": published_at,
        "locked": locked,
    })


def _scenarios(ctx, sop_cycles, n=10):
    rng = ctx.rng
    cycle_ids = rng.choice(sop_cycles["cycle_id"].to_numpy(), size=n)
    types = weighted_choice(rng, SCENARIO_TYPES, SCENARIO_TYPE_W, n)
    return pd.DataFrame({
        "scenario_id": [f"SCN{i:04d}" for i in range(1, n + 1)],
        "cycle_id": cycle_ids,
        "scenario_name": [f"{t.replace('_',' ').title()} scenario {i}" for i, t in enumerate(types, start=1)],
        "scenario_type": types,
        "description": [
            "10% upside in NA retail tied to Q3 marketing surge.",
            "Tariff: 25% on imports from CN, reroute through MX.",
            "Disruption: 4-week plant outage at Hamburg line 3.",
            "Capacity invest: add second shift at Plano DC.",
            "New product launch: Ramp curve for ITM0000123 (EMEA).",
            "EOL accelerated for ITM0000777 — clear by Q4.",
            "Downside: 8% demand softness in APAC ecom.",
            "Base plan, no shocks.",
            "Tariff retaliation on EU exports to BR.",
            "Capacity invest: qualify alternate co-manufacturer.",
        ][:n],
        "created_by": rng.choice(["s.planner1", "s.planner2", "ibp.lead", "vp.plan"], size=n),
        "created_at": pd.Timestamp("2026-05-01") - pd.to_timedelta(rng.integers(1, 90, size=n), unit="D"),
        "published_at": pd.Timestamp("2026-05-08"),
        "status": weighted_choice(rng, SCENARIO_STATUS, SCENARIO_STATUS_W, n),
        "revenue_impact_usd": np.round(rng.normal(0, 4_500_000, size=n), 2),
        "working_capital_impact_usd": np.round(rng.normal(0, 1_800_000, size=n), 2),
        "service_level_impact_pct": np.round(rng.normal(0, 2.4, size=n), 2),
    })


def _supply_plans(ctx, items, locations, sop_cycles, scenarios, n=100_000):
    rng = ctx.rng
    it_idx = rng.integers(0, len(items), size=n)
    lc_idx = rng.integers(0, len(locations), size=n)
    src_idx = rng.integers(0, len(locations), size=n)
    cycle_id = rng.choice(sop_cycles["cycle_id"].to_numpy(), size=n)
    # Most rows in published plan (no scenario_id), 20% under a scenario
    has_scn = rng.random(n) < 0.20
    scenario_id = np.where(has_scn,
                           rng.choice(scenarios["scenario_id"].to_numpy(), size=n),
                           None)
    week_offsets = rng.integers(0, 26, size=n)
    period_start = pd.to_datetime("2026-05-04") + pd.to_timedelta(week_offsets * 7, unit="D")
    planned_units = np.round(rng.lognormal(3.6, 1.1, size=n), 4)
    unit_cost = items["unit_cost"].to_numpy()[it_idx]
    planned_value = np.round(planned_units * unit_cost, 4)
    return pd.DataFrame({
        "supply_plan_id": np.arange(1, n + 1, dtype=np.int64),
        "item_id": items["item_id"].to_numpy()[it_idx],
        "location_id": locations["location_id"].to_numpy()[lc_idx],
        "source_location_id": locations["location_id"].to_numpy()[src_idx],
        "supply_type": weighted_choice(rng, SUPPLY_TYPES, SUPPLY_TYPE_W, n),
        "cycle_id": cycle_id,
        "scenario_id": scenario_id,
        "period_start": period_start,
        "period_grain": "week",
        "planned_units": planned_units,
        "planned_value": planned_value,
        "lead_time_days": rng.integers(1, 90, size=n).astype(np.int16),
        "status": weighted_choice(rng, SUPPLY_STATUS, SUPPLY_STATUS_W, n),
        "published_at": pd.Timestamp("2026-05-08"),
    })


def _inventory_positions(ctx, items, locations, n=200_000):
    rng = ctx.rng
    it_idx = rng.integers(0, len(items), size=n)
    lc_idx = rng.integers(0, len(locations), size=n)
    snapshot_ts = pd.Timestamp("2026-05-01") - pd.to_timedelta(rng.integers(0, 30, size=n), unit="D")
    on_hand = np.round(rng.lognormal(4.6, 1.2, size=n), 4)
    on_order = np.round(on_hand * rng.uniform(0.1, 1.0, size=n), 4)
    in_transit = np.round(on_hand * rng.uniform(0.0, 0.6, size=n), 4)
    allocated = np.round(on_hand * rng.uniform(0.0, 0.55, size=n), 4)
    safety_stock = np.round(on_hand * rng.uniform(0.10, 0.45, size=n), 4)
    reorder_point = np.round(safety_stock * rng.uniform(1.2, 2.5, size=n), 4)
    unit_cost = items["unit_cost"].to_numpy()[it_idx]
    inv_value = np.round(on_hand * unit_cost, 4)
    avg_daily = np.clip(rng.lognormal(2.0, 0.8, size=n), 0.1, None)
    doh_days = np.round(on_hand / avg_daily, 2)
    excess = np.clip(on_hand - safety_stock * 1.4, 0, None)
    excess = np.round(excess, 4)
    stockout = (on_hand < safety_stock * 0.5)
    return pd.DataFrame({
        "inventory_position_id": np.arange(1, n + 1, dtype=np.int64),
        "item_id": items["item_id"].to_numpy()[it_idx],
        "location_id": locations["location_id"].to_numpy()[lc_idx],
        "snapshot_ts": snapshot_ts,
        "on_hand_units": on_hand,
        "on_order_units": on_order,
        "in_transit_units": in_transit,
        "allocated_units": allocated,
        "safety_stock_units": safety_stock,
        "reorder_point_units": reorder_point,
        "inventory_value": inv_value,
        "doh_days": doh_days,
        "excess_units": excess,
        "stockout_flag": stockout,
    })


def _capacity(ctx, locations, n=50):
    rng = ctx.rng
    lc_idx = rng.integers(0, len(locations), size=n)
    res_type = weighted_choice(rng, RESOURCE_TYPES, RESOURCE_TYPE_W, n)
    avail = np.round(rng.uniform(160, 720, size=n), 2)               # hours / period
    load = np.round(avail * rng.uniform(0.45, 1.05, size=n), 2)
    util = np.clip(np.round((load / avail) * 100, 2), 0, 130)
    return pd.DataFrame({
        "capacity_id": [f"CAP{i:05d}" for i in range(1, n + 1)],
        "location_id": locations["location_id"].to_numpy()[lc_idx],
        "resource_id": [f"RES{i:05d}" for i in range(1, n + 1)],
        "resource_type": res_type,
        "period_start": pd.Timestamp("2026-05-04") + pd.to_timedelta(
            rng.integers(0, 26, size=n) * 7, unit="D"),
        "period_grain": "week",
        "available_hours": avail,
        "planned_load_hours": load,
        "utilization_pct": util,
        "changeover_hours": np.round(rng.uniform(0, 24, size=n), 2),
        "status": weighted_choice(rng, CAP_STATUS, CAP_STATUS_W, n),
    })


def _bom(ctx, items, locations, n=8_000):
    """Sparse BOM: each parent has 1-6 children. Materialize ~8k links."""
    rng = ctx.rng
    parent_idx = rng.integers(0, len(items), size=n)
    component_idx = rng.integers(0, len(items), size=n)
    # Avoid self-references
    same = (parent_idx == component_idx)
    component_idx[same] = (component_idx[same] + 1) % len(items)
    loc_idx = rng.integers(0, len(locations), size=n)
    eff_from = pd.Timestamp("2024-01-01") + pd.to_timedelta(rng.integers(0, 700, size=n), unit="D")
    eff_to = eff_from + pd.to_timedelta(rng.integers(180, 3 * 365, size=n), unit="D")
    return pd.DataFrame({
        "bom_id": [f"BOM{i:07d}" for i in range(1, n + 1)],
        "parent_item_id": items["item_id"].to_numpy()[parent_idx],
        "component_item_id": items["item_id"].to_numpy()[component_idx],
        "location_id": locations["location_id"].to_numpy()[loc_idx],
        "quantity_per": np.round(rng.lognormal(0.0, 0.6, size=n), 6),
        "yield_pct": np.round(rng.uniform(0.85, 1.0, size=n) * 100, 2),
        "effective_from": eff_from,
        "effective_to": eff_to,
        "bom_version": rng.choice(["v1", "v2", "v3"], size=n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating items...")
    items = _items(ctx)
    print("  generating locations...")
    locations = _locations(ctx)
    print("  generating customers...")
    customers = _customers(ctx)
    print("  generating sop_cycles...")
    cycles = _sop_cycles(ctx)
    print("  generating sales_history...")
    sales = _sales_history(ctx, items, locations, customers)
    print("  generating scenarios...")
    scenarios = _scenarios(ctx, cycles)
    print("  generating forecasts (1.56M rows)...")
    forecasts = _forecasts(ctx, items, locations, customers, cycles)
    print("  generating supply_plans...")
    supply = _supply_plans(ctx, items, locations, cycles, scenarios)
    print("  generating inventory_positions...")
    inv = _inventory_positions(ctx, items, locations)
    print("  generating capacity...")
    cap = _capacity(ctx, locations)
    print("  generating bom...")
    bom = _bom(ctx, items, locations)

    tables = {
        "item": items,
        "location": locations,
        "customer": customers,
        "sop_cycle": cycles,
        "sales_history": sales,
        "scenario": scenarios,
        "forecast": forecasts,
        "supply_plan": supply,
        "inventory_position": inv,
        "capacity": cap,
        "bom": bom,
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
