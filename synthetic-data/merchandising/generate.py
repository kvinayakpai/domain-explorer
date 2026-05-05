"""
Synthetic Merchandising data.

Entities (>=8): vendors, products, stores, prices, promotions,
inventory_snapshots, sales_lines, markdowns, replenishment_orders, returns.
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

SUBDOMAIN = "merchandising"


def _vendors(ctx, n=10_000):
    f = ctx.faker
    rng = ctx.rng
    return pd.DataFrame({
        "vendor_id": [f"VND{i:06d}" for i in range(1, n + 1)],
        "vendor_name": [f.company() for _ in range(n)],
        "country": rng.choice(country_codes(), size=n),
        "tier": weighted_choice(rng, ["strategic", "preferred", "standard", "tail"], [0.05, 0.20, 0.55, 0.20], n),
        "lead_time_days": rng.integers(2, 90, size=n),
        "active": rng.random(n) < 0.95,
    })


def _products(ctx, vendors, n=20_000):
    rng = ctx.rng
    f = ctx.faker
    cats = ["Apparel", "Footwear", "Home", "Beauty", "Grocery", "Electronics", "Toys", "Sports", "Accessories"]
    return pd.DataFrame({
        "sku": [f"SKU{i:08d}" for i in range(1, n + 1)],
        "product_name": [f.bs().title() for _ in range(n)],
        "vendor_id": rng.choice(vendors["vendor_id"].to_numpy(), size=n),
        "category": rng.choice(cats, size=n),
        "subcategory": [f.word() for _ in range(n)],
        "msrp": np.round(rng.gamma(2.0, 25, size=n), 2),
        "cost": np.round(rng.gamma(2.0, 12, size=n), 2),
        "launch_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2018-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "active": rng.random(n) < 0.85,
    })


def _stores(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "store_id": [f"STR{i:05d}" for i in range(1, n + 1)],
        "store_name": [f"{f.city()} Store" for _ in range(n)],
        "country": rng.choice(country_codes(), size=n),
        "region": weighted_choice(rng, ["NA", "EMEA", "APAC", "LATAM"], [0.45, 0.30, 0.15, 0.10], n),
        "format": weighted_choice(rng, ["full_line", "small_format", "outlet", "popup", "ecom_dc"], [0.50, 0.20, 0.15, 0.05, 0.10], n),
        "open_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2000-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s").date,
        "active": rng.random(n) < 0.93,
    })


def _prices(ctx, products, stores, n_min=200_000):
    rng = ctx.rng
    n = max(n_min, 200_000)
    pids = rng.choice(products["sku"].to_numpy(), size=n)
    sids = rng.choice(stores["store_id"].to_numpy(), size=n)
    msrp_lookup = dict(zip(products["sku"], products["msrp"], strict=False))
    base = np.array([msrp_lookup[s] for s in pids])
    factor = rng.uniform(0.7, 1.1, size=n)
    return pd.DataFrame({
        "price_id": [f"PRC{i:010d}" for i in range(1, n + 1)],
        "sku": pids,
        "store_id": sids,
        "list_price": np.round(base * factor, 2),
        "currency": rng.choice(["USD", "EUR", "GBP", "JPY"], size=n),
        "effective_from": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "channel": weighted_choice(rng, ["store", "ecom", "marketplace"], [0.55, 0.35, 0.10], n),
    })


def _promotions(ctx, products, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "promo_id": [f"PROMO{i:07d}" for i in range(1, n + 1)],
        "name": rng.choice(["Spring Sale", "Holiday", "Markdown", "BOGO", "Clearance", "Flash Deal", "Loyalty"], size=n),
        "sku": rng.choice(products["sku"].to_numpy(), size=n),
        "discount_pct": np.round(rng.uniform(0.05, 0.7, size=n), 2),
        "start_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "duration_days": rng.integers(1, 30, size=n),
        "channel": weighted_choice(rng, ["all", "ecom_only", "store_only"], [0.55, 0.30, 0.15], n),
    })


def _inventory(ctx, products, stores, n=300_000):
    rng = ctx.rng
    return pd.DataFrame({
        "snapshot_id": [f"INV{i:010d}" for i in range(1, n + 1)],
        "sku": rng.choice(products["sku"].to_numpy(), size=n),
        "store_id": rng.choice(stores["store_id"].to_numpy(), size=n),
        "on_hand": rng.integers(0, 500, size=n),
        "on_order": rng.integers(0, 200, size=n),
        "safety_stock": rng.integers(0, 50, size=n),
        "as_of": daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
    })


def _sales(ctx, products, stores, n=400_000):
    rng = ctx.rng
    qty = rng.integers(1, 8, size=n)
    pid = rng.choice(products["sku"].to_numpy(), size=n)
    msrp_lookup = dict(zip(products["sku"], products["msrp"], strict=False))
    unit_price = np.array([msrp_lookup[p] for p in pid]) * rng.uniform(0.4, 1.05, size=n)
    return pd.DataFrame({
        "sale_line_id": [f"SLE{i:010d}" for i in range(1, n + 1)],
        "sku": pid,
        "store_id": rng.choice(stores["store_id"].to_numpy(), size=n),
        "quantity": qty,
        "unit_price": np.round(unit_price, 2),
        "extended_amount": np.round(qty * unit_price, 2),
        "ts": daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
        "channel": weighted_choice(rng, ["store", "ecom", "marketplace"], [0.55, 0.35, 0.10], n),
    })


def _markdowns(ctx, products, n=15_000):
    rng = ctx.rng
    return pd.DataFrame({
        "markdown_id": [f"MD{i:08d}" for i in range(1, n + 1)],
        "sku": rng.choice(products["sku"].to_numpy(), size=n),
        "applied_at": daterange_minutes(rng, n, pd.Timestamp("2024-06-01"), pd.Timestamp("2026-04-30")),
        "depth_pct": np.round(rng.uniform(0.10, 0.80, size=n), 2),
        "reason": weighted_choice(rng, ["aged_stock", "seasonal", "competitive", "damaged", "promo"], [0.30, 0.30, 0.15, 0.10, 0.15], n),
    })


def _replenishment(ctx, products, stores, n=20_000):
    rng = ctx.rng
    return pd.DataFrame({
        "po_id": [f"RPO{i:08d}" for i in range(1, n + 1)],
        "sku": rng.choice(products["sku"].to_numpy(), size=n),
        "store_id": rng.choice(stores["store_id"].to_numpy(), size=n),
        "quantity": rng.integers(10, 1000, size=n),
        "ordered_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
        "expected_at": daterange_minutes(rng, n, pd.Timestamp("2024-02-01"), pd.Timestamp("2026-06-30")),
        "status": weighted_choice(rng, ["open", "received", "cancelled", "partial"], [0.20, 0.65, 0.05, 0.10], n),
    })


def _returns(ctx, sales, n_min=10_000):
    rng = ctx.rng
    return_idx = rng.choice(len(sales), size=int(len(sales) * 0.04), replace=False)
    n = max(n_min, len(return_idx))
    if n > len(return_idx):
        extra = n - len(return_idx)
        return_idx = np.concatenate([return_idx, rng.choice(len(sales), size=extra)])
    sub = sales.iloc[return_idx].reset_index(drop=True)
    n = len(sub)
    return pd.DataFrame({
        "return_id": [f"RTN{i:09d}" for i in range(1, n + 1)],
        "sale_line_id": sub["sale_line_id"].to_numpy(),
        "sku": sub["sku"].to_numpy(),
        "quantity": sub["quantity"].to_numpy(),
        "amount": sub["extended_amount"].to_numpy(),
        "reason": weighted_choice(rng, ["wrong_size", "defective", "changed_mind", "wrong_item", "damaged_in_transit"], [0.30, 0.20, 0.30, 0.10, 0.10], n),
        "returned_at": pd.to_datetime(sub["ts"].to_numpy()) + pd.to_timedelta(rng.integers(1, 60, size=n), unit="D"),
    })


def generate(seed=42):
    ctx = make_context(seed)
    vendors = _vendors(ctx)
    products = _products(ctx, vendors)
    stores = _stores(ctx)
    prices = _prices(ctx, products, stores)
    promos = _promotions(ctx, products)
    inv = _inventory(ctx, products, stores)
    sales = _sales(ctx, products, stores)
    markdowns = _markdowns(ctx, products)
    repl = _replenishment(ctx, products, stores)
    returns_ = _returns(ctx, sales)
    tables = {
        "vendors": vendors,
        "products": products,
        "stores": stores,
        "prices": prices,
        "promotions": promos,
        "inventory_snapshots": inv,
        "sales_lines": sales,
        "markdowns": markdowns,
        "replenishment_orders": repl,
        "returns": returns_,
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
