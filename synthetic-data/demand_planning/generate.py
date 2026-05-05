"""
Synthetic Demand Planning data.

Entities (>=8): items, locations, customers_b2b, historical_demand,
forecasts, promotions, shipments, inventory_positions, calendar_periods, forecast_errors.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    country_codes,
    daterange_minutes,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "demand_planning"


def _items(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    cats = ["RawMaterial", "Component", "FinishedGood", "Spare", "Packaging"]
    return pd.DataFrame({
        "item_id": [f"ITM{i:07d}" for i in range(1, n + 1)],
        "item_name": [f.bs().title() for _ in range(n)],
        "category": rng.choice(cats, size=n),
        "abc_class": weighted_choice(rng, ["A", "B", "C"], [0.20, 0.30, 0.50], n),
        "lead_time_days": rng.integers(1, 90, size=n),
        "unit_cost": np.round(rng.gamma(2.0, 6.0, size=n), 2),
        "shelf_life_days": rng.integers(30, 730, size=n),
    })


def _locations(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "location_id": [f"LOC{i:05d}" for i in range(1, n + 1)],
        "location_name": [f"{f.city()} {rng.choice(['DC','RDC','Plant','Hub'])}" for _ in range(n)],
        "type": weighted_choice(rng, ["dc", "factory", "store", "3pl", "supplier_vmi"], [0.35, 0.20, 0.30, 0.10, 0.05], n),
        "country": rng.choice(country_codes(), size=n),
        "capacity_units": rng.integers(1000, 1_000_000, size=n),
    })


def _customers_b2b(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "customer_id": [f"B2B{i:06d}" for i in range(1, n + 1)],
        "name": [f.company() for _ in range(n)],
        "channel": weighted_choice(rng, ["wholesale", "retail_chain", "industrial", "ecom_marketplace", "direct"], [0.30, 0.30, 0.20, 0.10, 0.10], n),
        "credit_limit": np.round(rng.gamma(3.0, 12000, size=n), 2),
        "country": rng.choice(country_codes(), size=n),
        "tier": weighted_choice(rng, ["platinum", "gold", "silver", "bronze"], [0.05, 0.20, 0.40, 0.35], n),
    })


def _calendar(ctx, n=12_000):
    # 12k consecutive days from 2018-01-01
    start = pd.Timestamp("2018-01-01")
    days = pd.date_range(start, periods=n, freq="D")
    rng = ctx.rng
    return pd.DataFrame({
        "period_id": [f"D{d.strftime('%Y%m%d')}" for d in days],
        "date": days.date,
        "iso_week": [d.isocalendar()[1] for d in days],
        "fiscal_quarter": [(d.month - 1) // 3 + 1 for d in days],
        "is_weekend": np.isin(days.dayofweek, [5, 6]),
        "is_holiday": rng.random(n) < 0.03,
    })


def _historical_demand(ctx, items, locations, n=120_000):
    rng = ctx.rng
    qty = rng.gamma(3.0, 8.0, size=n)
    season = 1 + 0.3 * np.sin(2 * np.pi * (rng.integers(0, 52, size=n) / 52))
    return pd.DataFrame({
        "demand_id": [f"DMD{i:010d}" for i in range(1, n + 1)],
        "item_id": rng.choice(items["item_id"].to_numpy(), size=n),
        "location_id": rng.choice(locations["location_id"].to_numpy(), size=n),
        "period_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2022-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "quantity": np.round(qty * season, 2),
        "channel": weighted_choice(rng, ["direct", "wholesale", "retail", "ecom"], [0.30, 0.30, 0.25, 0.15], n),
    })


def _forecasts(ctx, items, locations, n=80_000):
    rng = ctx.rng
    base = rng.gamma(3.0, 8.0, size=n)
    return pd.DataFrame({
        "forecast_id": [f"FCT{i:010d}" for i in range(1, n + 1)],
        "item_id": rng.choice(items["item_id"].to_numpy(), size=n),
        "location_id": rng.choice(locations["location_id"].to_numpy(), size=n),
        "horizon_weeks": rng.integers(1, 53, size=n),
        "model": weighted_choice(rng, ["arima", "prophet", "ml_xgb", "ml_lstm", "ensemble", "manual"], [0.20, 0.15, 0.20, 0.10, 0.30, 0.05], n),
        "forecast_qty": np.round(base, 2),
        "lower_80": np.round(base * 0.85, 2),
        "upper_80": np.round(base * 1.15, 2),
        "generated_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
    })


def _promotions(ctx, items, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "promo_id": [f"DP{i:07d}" for i in range(1, n + 1)],
        "item_id": rng.choice(items["item_id"].to_numpy(), size=n),
        "promo_type": rng.choice(["price_cut", "bogo", "endcap", "feature", "bundle"], size=n),
        "lift_pct": np.round(rng.uniform(0.05, 1.0, size=n), 2),
        "start_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "duration_days": rng.integers(2, 60, size=n),
    })


def _shipments(ctx, items, locations, customers, n=80_000):
    rng = ctx.rng
    return pd.DataFrame({
        "shipment_id": [f"SHP{i:09d}" for i in range(1, n + 1)],
        "item_id": rng.choice(items["item_id"].to_numpy(), size=n),
        "from_location_id": rng.choice(locations["location_id"].to_numpy(), size=n),
        "customer_id": rng.choice(customers["customer_id"].to_numpy(), size=n),
        "quantity": rng.integers(1, 5000, size=n),
        "shipped_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
        "delivered_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-05"), pd.Timestamp("2026-05-31")),
        "carrier": rng.choice(["UPS", "FedEx", "DHL", "Maersk", "DB Schenker", "Local"], size=n),
        "on_time": rng.random(n) < 0.93,
    })


def _inventory_positions(ctx, items, locations, n=80_000):
    rng = ctx.rng
    return pd.DataFrame({
        "position_id": [f"INVP{i:09d}" for i in range(1, n + 1)],
        "item_id": rng.choice(items["item_id"].to_numpy(), size=n),
        "location_id": rng.choice(locations["location_id"].to_numpy(), size=n),
        "on_hand": rng.integers(0, 50_000, size=n),
        "in_transit": rng.integers(0, 5_000, size=n),
        "reserved": rng.integers(0, 1_000, size=n),
        "as_of": daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
    })


def _forecast_errors(ctx, forecasts, n_min=10_000):
    rng = ctx.rng
    n = min(len(forecasts), max(n_min, len(forecasts)))
    sub = forecasts.sample(n=n, random_state=ctx.seed) if len(forecasts) >= n else forecasts
    actual = sub["forecast_qty"].to_numpy() * rng.normal(1.0, 0.2, size=len(sub))
    err = actual - sub["forecast_qty"].to_numpy()
    return pd.DataFrame({
        "error_id": [f"FERR{i:09d}" for i in range(1, len(sub) + 1)],
        "forecast_id": sub["forecast_id"].to_numpy(),
        "actual_qty": np.round(actual, 2),
        "error": np.round(err, 2),
        "ape": np.round(np.abs(err) / np.maximum(sub["forecast_qty"].to_numpy(), 1.0), 4),
        "computed_at": daterange_minutes(rng, len(sub), pd.Timestamp("2024-02-01"), pd.Timestamp("2026-04-30")),
    })


def generate(seed=42):
    ctx = make_context(seed)
    items = _items(ctx)
    locations = _locations(ctx)
    customers = _customers_b2b(ctx)
    cal = _calendar(ctx)
    demand = _historical_demand(ctx, items, locations)
    fcst = _forecasts(ctx, items, locations)
    promos = _promotions(ctx, items)
    shipments = _shipments(ctx, items, locations, customers)
    inv = _inventory_positions(ctx, items, locations)
    errors = _forecast_errors(ctx, fcst)

    tables = {
        "items": items,
        "locations": locations,
        "customers_b2b": customers,
        "calendar_periods": cal,
        "historical_demand": demand,
        "forecasts": fcst,
        "promotions": promos,
        "shipments": shipments,
        "inventory_positions": inv,
        "forecast_errors": errors,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
