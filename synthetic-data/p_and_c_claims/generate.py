"""
Synthetic Property & Casualty Claims data.

Entities (>=8): policyholders, policies, vehicles, properties, claims,
claim_lines, payments_to_claimants, reserves, fnol_events, adjusters.
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

SUBDOMAIN = "p_and_c_claims"


def _policyholders(ctx, n=10_000):
    f = ctx.faker
    rng = ctx.rng
    return pd.DataFrame({
        "policyholder_id": [f"PH{i:08d}" for i in range(1, n + 1)],
        "full_name": [f.name() for _ in range(n)],
        "email": [f.unique.email() for _ in range(n)],
        "country": rng.choice(country_codes(), size=n),
        "credit_band": weighted_choice(rng, ["A", "B", "C", "D"], [0.25, 0.40, 0.25, 0.10], n),
        "tenure_years": rng.integers(0, 25, size=n),
    })


def _policies(ctx, holders, n=15_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "policy_id": [f"POL{i:08d}" for i in range(1, n + 1)],
        "policyholder_id": rng.choice(holders["policyholder_id"].to_numpy(), size=n),
        "line_of_business": weighted_choice(rng, ["auto", "home", "umbrella", "commercial"], [0.55, 0.30, 0.05, 0.10], n),
        "premium_annual": np.round(rng.gamma(2.0, 700, size=n), 2),
        "deductible": rng.choice([250, 500, 1000, 2500], size=n),
        "effective_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2022-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s").date,
        "expires_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2027-12-31").timestamp()), size=n), unit="s").date,
        "carrier": rng.choice(["Allianz", "Zurich", "AXA", "Liberty", "Travelers", "Chubb", "Munich Re"], size=n),
    })


def _vehicles(ctx, policies, n=12_000):
    rng = ctx.rng
    auto_pol = policies[policies["line_of_business"] == "auto"]
    pids = rng.choice(auto_pol["policy_id"].to_numpy(), size=n)
    return pd.DataFrame({
        "vehicle_id": [f"VEH{i:08d}" for i in range(1, n + 1)],
        "policy_id": pids,
        "make": rng.choice(["Toyota", "Ford", "Honda", "BMW", "VW", "Tesla", "Hyundai", "Chevrolet"], size=n),
        "model_year": rng.integers(2008, 2026, size=n),
        "vin": [f"{rng.integers(1_000_000_000, 9_999_999_999)}" for _ in range(n)],
        "annual_mileage": rng.integers(2000, 30000, size=n),
        "primary_use": weighted_choice(rng, ["commute", "pleasure", "business"], [0.65, 0.25, 0.10], n),
    })


def _properties(ctx, policies, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    home_pol = policies[policies["line_of_business"].isin(["home", "commercial"])]
    pids = rng.choice(home_pol["policy_id"].to_numpy(), size=n)
    return pd.DataFrame({
        "property_id": [f"PRP{i:08d}" for i in range(1, n + 1)],
        "policy_id": pids,
        "property_type": weighted_choice(rng, ["single_family", "condo", "multi_unit", "commercial"], [0.55, 0.20, 0.15, 0.10], n),
        "year_built": rng.integers(1900, 2026, size=n),
        "square_feet": rng.integers(600, 6000, size=n),
        "construction": weighted_choice(rng, ["frame", "brick", "concrete", "mixed"], [0.55, 0.25, 0.15, 0.05], n),
        "fire_protection_class": rng.integers(1, 11, size=n),
        "zip": [f.postcode() for _ in range(n)],
    })


def _adjusters(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "adjuster_id": [f"ADJ{i:06d}" for i in range(1, n + 1)],
        "name": [f.name() for _ in range(n)],
        "specialty": weighted_choice(rng, ["auto", "property", "complex", "fraud", "general"], [0.40, 0.30, 0.10, 0.05, 0.15], n),
        "license_state": rng.choice(["CA", "TX", "NY", "FL", "IL", "OH", "PA", "WA"], size=n),
        "experience_years": rng.integers(0, 30, size=n),
        "active": rng.random(n) < 0.92,
    })


def _claims(ctx, policies, adjusters, n=80_000):
    rng = ctx.rng
    pols = rng.choice(policies["policy_id"].to_numpy(), size=n)
    fnol = daterange_minutes(rng, n, pd.Timestamp("2023-01-01"), pd.Timestamp("2026-04-30"))
    severity = weighted_choice(rng, ["low", "medium", "high", "catastrophic"], [0.55, 0.30, 0.12, 0.03], n)
    sev_amount_base = {"low": (300, 0.6), "medium": (3500, 0.7), "high": (25000, 0.8), "catastrophic": (180000, 1.0)}
    base_means = np.array([sev_amount_base[s][0] for s in severity])
    base_sigma = np.array([sev_amount_base[s][1] for s in severity])
    incurred = np.round(np.exp(np.log(base_means) + rng.normal(0, base_sigma, n)), 2)
    return pd.DataFrame({
        "claim_id": [f"CLM{i:09d}" for i in range(1, n + 1)],
        "policy_id": pols,
        "adjuster_id": rng.choice(adjusters["adjuster_id"].to_numpy(), size=n),
        "fnol_ts": fnol,
        "loss_date": fnol - pd.to_timedelta(rng.integers(0, 30, size=n), unit="D"),
        "peril": weighted_choice(rng, ["collision", "theft", "fire", "wind", "water", "liability", "hail", "vandalism"], [0.30, 0.10, 0.08, 0.12, 0.10, 0.15, 0.10, 0.05], n),
        "severity": severity,
        "status": weighted_choice(rng, ["open", "closed_paid", "closed_denied", "in_litigation"], [0.20, 0.65, 0.10, 0.05], n),
        "incurred_amount": incurred,
        "fraud_score": np.round(rng.beta(1.5, 8, size=n), 4),
    })


def _claim_lines(ctx, claims, n_target=120_000):
    rng = ctx.rng
    # 1-3 lines per claim
    counts = rng.integers(1, 4, size=len(claims))
    expanded_claim_ids = np.repeat(claims["claim_id"].to_numpy(), counts)
    n = len(expanded_claim_ids)
    if n < n_target:
        # fill with extras
        extras = rng.choice(claims["claim_id"].to_numpy(), size=n_target - n)
        expanded_claim_ids = np.concatenate([expanded_claim_ids, extras])
        n = len(expanded_claim_ids)
    return pd.DataFrame({
        "claim_line_id": [f"CL{i:010d}" for i in range(1, n + 1)],
        "claim_id": expanded_claim_ids,
        "coverage": weighted_choice(rng, ["bodily_injury", "property_damage", "collision", "comprehensive", "medical", "uninsured_motorist", "dwelling", "contents"], [0.10, 0.20, 0.20, 0.15, 0.10, 0.05, 0.10, 0.10], n),
        "amount": np.round(np.exp(rng.normal(7.5, 1.0, n)), 2),
        "status": weighted_choice(rng, ["paid", "approved", "denied", "pending"], [0.65, 0.15, 0.10, 0.10], n),
    })


def _payments(ctx, claim_lines, n_min=10_000):
    rng = ctx.rng
    paid = claim_lines[claim_lines["status"].isin(["paid", "approved"])]
    n = max(n_min, len(paid))
    if n > len(paid):
        # supplement
        extra = n - len(paid)
        ids = np.concatenate([paid["claim_line_id"].to_numpy(), rng.choice(claim_lines["claim_line_id"].to_numpy(), size=extra)])
        amts = np.concatenate([paid["amount"].to_numpy(), np.round(np.exp(rng.normal(7.0, 0.9, extra)), 2)])
    else:
        ids = paid["claim_line_id"].to_numpy()
        amts = paid["amount"].to_numpy()
    n = len(ids)
    return pd.DataFrame({
        "payment_id": [f"CPY{i:010d}" for i in range(1, n + 1)],
        "claim_line_id": ids,
        "amount": amts,
        "method": weighted_choice(rng, ["check", "ach", "wire", "card_refund"], [0.45, 0.40, 0.10, 0.05], n),
        "paid_at": daterange_minutes(rng, n, pd.Timestamp("2023-02-01"), pd.Timestamp("2026-04-30")),
    })


def _reserves(ctx, claims):
    rng = ctx.rng
    n = len(claims)
    return pd.DataFrame({
        "reserve_id": [f"RSV{i:09d}" for i in range(1, n + 1)],
        "claim_id": claims["claim_id"].to_numpy(),
        "reserve_amount": np.round(claims["incurred_amount"].to_numpy() * rng.uniform(0.7, 1.3, size=n), 2),
        "category": weighted_choice(rng, ["indemnity", "expense", "salvage", "subrogation"], [0.65, 0.20, 0.05, 0.10], n),
        "set_at": daterange_minutes(rng, n, pd.Timestamp("2023-01-15"), pd.Timestamp("2026-04-30")),
    })


def _fnol_events(ctx, claims):
    rng = ctx.rng
    n = len(claims)
    return pd.DataFrame({
        "fnol_event_id": [f"FNL{i:09d}" for i in range(1, n + 1)],
        "claim_id": claims["claim_id"].to_numpy(),
        "channel": weighted_choice(rng, ["phone", "web", "mobile_app", "agent", "email"], [0.40, 0.20, 0.20, 0.15, 0.05], n),
        "duration_minutes": np.round(rng.gamma(2.0, 6.0, size=n), 1),
        "language": weighted_choice(rng, ["en", "es", "fr", "de"], [0.75, 0.15, 0.05, 0.05], n),
        "received_at": claims["fnol_ts"].to_numpy(),
    })


def generate(seed=42):
    ctx = make_context(seed)
    holders = _policyholders(ctx)
    policies = _policies(ctx, holders)
    vehicles = _vehicles(ctx, policies)
    properties = _properties(ctx, policies)
    adjusters = _adjusters(ctx)
    claims = _claims(ctx, policies, adjusters)
    claim_lines = _claim_lines(ctx, claims)
    payments = _payments(ctx, claim_lines)
    reserves = _reserves(ctx, claims)
    fnol = _fnol_events(ctx, claims)

    tables = {
        "policyholders": holders,
        "policies": policies,
        "vehicles": vehicles,
        "properties": properties,
        "adjusters": adjusters,
        "claims": claims,
        "claim_lines": claim_lines,
        "claim_payments": payments,
        "reserves": reserves,
        "fnol_events": fnol,
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
