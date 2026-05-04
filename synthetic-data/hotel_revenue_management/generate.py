"""
Synthetic Hotel Revenue Management data.

Entities (>=8): properties, room_types, rate_plans, channels,
guests, reservations, daily_inventory, daily_pricing, ancillaries, cancellations.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    country_codes,
    daterange_minutes,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "hotel_revenue_management"


def _properties(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "property_id": [f"HTL{i:05d}" for i in range(1, n + 1)],
        "name": [f"{f.last_name()} {rng.choice(['Inn','Hotel','Suites','Resort','Lodge'])}" for _ in range(n)],
        "city": [f.city() for _ in range(n)],
        "country": rng.choice(country_codes(), size=n),
        "brand": rng.choice(["Marriott", "Hilton", "Hyatt", "IHG", "Accor", "Indie", "Wyndham"], size=n),
        "stars": rng.choice([2, 3, 4, 5], p=[0.10, 0.40, 0.35, 0.15], size=n),
        "rooms": rng.integers(40, 800, size=n),
        "active": rng.random(n) < 0.97,
    })


def _room_types(ctx, properties, n=15_000):
    rng = ctx.rng
    return pd.DataFrame({
        "room_type_id": [f"RM{i:07d}" for i in range(1, n + 1)],
        "property_id": rng.choice(properties["property_id"].to_numpy(), size=n),
        "name": rng.choice(["Standard King", "Standard Double", "Deluxe King", "Junior Suite", "Suite", "Penthouse", "Family Room"], size=n),
        "max_occupancy": rng.choice([2, 3, 4, 6], p=[0.55, 0.20, 0.20, 0.05], size=n),
        "view": weighted_choice(rng, ["city", "ocean", "garden", "interior"], [0.35, 0.20, 0.20, 0.25], n),
        "size_sqm": rng.integers(18, 90, size=n),
    })


def _rate_plans(ctx, properties, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "rate_plan_id": [f"RP{i:07d}" for i in range(1, n + 1)],
        "property_id": rng.choice(properties["property_id"].to_numpy(), size=n),
        "name": rng.choice(["BAR", "Member Rate", "AAA", "Government", "Corporate", "Advance Purchase 14", "Advance Purchase 30", "Pkg + Breakfast"], size=n),
        "refundable": rng.random(n) < 0.7,
        "min_los": rng.integers(1, 7, size=n),
        "discount_pct": np.round(rng.uniform(0.0, 0.4, size=n), 2),
    })


def _channels(ctx, n=10_000):
    rng = ctx.rng
    base = ["Direct Web", "Direct Mobile", "Voice Reservations", "Booking.com", "Expedia", "Hotwire", "GDS - Sabre", "GDS - Amadeus", "Google Hotel Ads", "TripAdvisor", "Agoda", "Airbnb"]
    return pd.DataFrame({
        "channel_id": [f"CH{i:06d}" for i in range(1, n + 1)],
        "name": rng.choice(base, size=n),
        "category": weighted_choice(rng, ["direct", "ota", "gds", "wholesaler", "metasearch"], [0.30, 0.40, 0.10, 0.10, 0.10], n),
        "commission_pct": np.round(rng.uniform(0.0, 0.25, size=n), 3),
        "active": rng.random(n) < 0.94,
    })


def _guests(ctx, n=20_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "guest_id": [f"GST{i:08d}" for i in range(1, n + 1)],
        "name": [f.name() for _ in range(n)],
        "country": rng.choice(country_codes(), size=n),
        "loyalty_tier": weighted_choice(rng, ["none", "silver", "gold", "platinum", "diamond"], [0.55, 0.20, 0.15, 0.07, 0.03], n),
        "lifetime_nights": rng.integers(0, 600, size=n),
    })


def _reservations(ctx, properties, room_types, rate_plans, channels, guests, n=120_000):
    rng = ctx.rng
    rt = room_types.sample(n=n, replace=True, random_state=ctx.seed)
    rt = rt.reset_index(drop=True)
    arrivals = pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-09-30").timestamp()), size=n), unit="s").date
    los = rng.choice([1, 2, 3, 4, 5, 7, 10, 14], p=[0.20, 0.30, 0.20, 0.10, 0.10, 0.05, 0.03, 0.02], size=n)
    departure = pd.to_datetime(arrivals) + pd.to_timedelta(los, unit="D")
    rate = np.round(rng.gamma(2.0, 80, size=n), 2)
    return pd.DataFrame({
        "reservation_id": [f"RES{i:09d}" for i in range(1, n + 1)],
        "property_id": rt["property_id"].to_numpy(),
        "room_type_id": rt["room_type_id"].to_numpy(),
        "rate_plan_id": rng.choice(rate_plans["rate_plan_id"].to_numpy(), size=n),
        "channel_id": rng.choice(channels["channel_id"].to_numpy(), size=n),
        "guest_id": rng.choice(guests["guest_id"].to_numpy(), size=n),
        "booked_at": daterange_minutes(rng, n, pd.Timestamp("2023-09-01"), pd.Timestamp("2026-09-15")),
        "arrival_date": arrivals,
        "departure_date": departure.date,
        "nights": los,
        "adr": rate,
        "total_amount": np.round(rate * los, 2),
        "status": weighted_choice(rng, ["confirmed", "checked_in", "checked_out", "cancelled", "no_show"], [0.10, 0.05, 0.70, 0.13, 0.02], n),
    })


def _daily_inventory(ctx, room_types, n=120_000):
    rng = ctx.rng
    n = max(n, 120_000)
    return pd.DataFrame({
        "inv_id": [f"INV{i:09d}" for i in range(1, n + 1)],
        "room_type_id": rng.choice(room_types["room_type_id"].to_numpy(), size=n),
        "stay_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-12-31").timestamp()), size=n), unit="s").date,
        "available": rng.integers(0, 80, size=n),
        "sold": rng.integers(0, 80, size=n),
        "out_of_order": rng.integers(0, 5, size=n),
    })


def _daily_pricing(ctx, room_types, rate_plans, n=120_000):
    rng = ctx.rng
    return pd.DataFrame({
        "pricing_id": [f"DPR{i:09d}" for i in range(1, n + 1)],
        "room_type_id": rng.choice(room_types["room_type_id"].to_numpy(), size=n),
        "rate_plan_id": rng.choice(rate_plans["rate_plan_id"].to_numpy(), size=n),
        "stay_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-12-31").timestamp()), size=n), unit="s").date,
        "rate": np.round(rng.gamma(2.0, 80, size=n), 2),
        "currency": rng.choice(["USD", "EUR", "GBP", "JPY"], size=n),
        "yield_score": np.round(rng.beta(2, 2, size=n), 3),
    })


def _ancillaries(ctx, reservations, n=80_000):
    rng = ctx.rng
    res_ids = rng.choice(reservations["reservation_id"].to_numpy(), size=n)
    return pd.DataFrame({
        "ancillary_id": [f"ANC{i:09d}" for i in range(1, n + 1)],
        "reservation_id": res_ids,
        "category": weighted_choice(rng, ["fnb", "spa", "parking", "wifi_premium", "early_checkin", "late_checkout", "tour", "minibar"], [0.30, 0.10, 0.15, 0.05, 0.10, 0.10, 0.10, 0.10], n),
        "amount": np.round(rng.gamma(2.0, 25, size=n), 2),
        "ts": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")),
    })


def _cancellations(ctx, reservations, n_min=10_000):
    rng = ctx.rng
    cancelled = reservations[reservations["status"].isin(["cancelled", "no_show"])]
    n = max(n_min, len(cancelled))
    if n > len(cancelled):
        extra = n - len(cancelled)
        sup = reservations.sample(n=extra, replace=True, random_state=ctx.seed)
        ids = np.concatenate([cancelled["reservation_id"].to_numpy(), sup["reservation_id"].to_numpy()])
        booked = np.concatenate([cancelled["booked_at"].to_numpy(), sup["booked_at"].to_numpy()])
    else:
        ids = cancelled["reservation_id"].to_numpy()
        booked = cancelled["booked_at"].to_numpy()
    n = len(ids)
    return pd.DataFrame({
        "cancellation_id": [f"CXL{i:09d}" for i in range(1, n + 1)],
        "reservation_id": ids,
        "cancelled_at": pd.to_datetime(booked) + pd.to_timedelta(rng.integers(1, 90, size=n), unit="D"),
        "reason": weighted_choice(rng, ["traveler_change", "weather", "price_drop", "no_show", "other"], [0.45, 0.15, 0.15, 0.15, 0.10], n),
        "fee_amount": np.round(rng.uniform(0, 200, size=n), 2),
    })


def generate(seed=42):
    ctx = make_context(seed)
    props = _properties(ctx)
    rooms = _room_types(ctx, props)
    rates = _rate_plans(ctx, props)
    channels = _channels(ctx)
    guests = _guests(ctx)
    res = _reservations(ctx, props, rooms, rates, channels, guests)
    inv = _daily_inventory(ctx, rooms)
    pricing = _daily_pricing(ctx, rooms, rates)
    anc = _ancillaries(ctx, res)
    cxl = _cancellations(ctx, res)
    tables = {
        "properties": props,
        "room_types": rooms,
        "rate_plans": rates,
        "channels": channels,
        "guests": guests,
        "reservations": res,
        "daily_inventory": inv,
        "daily_pricing": pricing,
        "ancillaries": anc,
        "cancellations": cxl,
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
