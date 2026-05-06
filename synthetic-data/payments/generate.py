"""
Synthetic Payments data.

Entities (>=8): customers, accounts, payment_instructions, payments,
settlements, chargebacks, disputes, fraud_alerts, mcc_codes (reference).

Run:
    python synthetic-data/payments/generate.py --seed 42
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Allow `python synthetic-data/payments/generate.py` direct invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (  # noqa: E402
    GenContext,
    country_codes,
    currency_codes,
    daterange_minutes,
    lognormal_amounts,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "payments"


def _customers(ctx: GenContext, n: int = 10_000) -> pd.DataFrame:
    rng = ctx.rng
    f = ctx.faker
    countries = np.array(country_codes())
    return pd.DataFrame(
        {
            "customer_id": [f"CUS{i:08d}" for i in range(1, n + 1)],
            "full_name": [f.name() for _ in range(n)],
            "email": [f.unique.email() for _ in range(n)],
            "country": rng.choice(countries, size=n),
            "kyc_status": weighted_choice(
                rng, ["verified", "pending", "rejected"], [0.88, 0.10, 0.02], n
            ),
            "risk_segment": weighted_choice(
                rng, ["low", "medium", "high"], [0.70, 0.25, 0.05], n
            ),
            "signup_date": pd.to_datetime(
                rng.integers(
                    int(pd.Timestamp("2018-01-01").timestamp()),
                    int(pd.Timestamp("2025-12-31").timestamp()),
                    size=n,
                ),
                unit="s",
            ).date,
        }
    )


def _accounts(ctx: GenContext, customers: pd.DataFrame, mult: float = 1.4) -> pd.DataFrame:
    rng = ctx.rng
    n = int(len(customers) * mult)
    cust_ids = rng.choice(customers["customer_id"].to_numpy(), size=n)
    return pd.DataFrame(
        {
            "account_id": [f"ACC{i:09d}" for i in range(1, n + 1)],
            "customer_id": cust_ids,
            "account_type": weighted_choice(
                rng, ["checking", "savings", "credit_card", "wallet"], [0.45, 0.20, 0.25, 0.10], n
            ),
            "currency": weighted_choice(rng, currency_codes(), [0.40, 0.20, 0.15, 0.05, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02], n),
            "open_date": pd.to_datetime(
                rng.integers(
                    int(pd.Timestamp("2018-01-01").timestamp()),
                    int(pd.Timestamp("2026-01-01").timestamp()),
                    size=n,
                ),
                unit="s",
            ).date,
            "status": weighted_choice(rng, ["active", "frozen", "closed"], [0.92, 0.04, 0.04], n),
        }
    )


def _mcc_assignments(ctx: GenContext, n: int = 10_000) -> pd.DataFrame:
    """
    Merchant-to-MCC assignment table (one row per merchant). Includes the canonical
    MCC reference set repeated and combined with synthesised merchant aliases so the
    table reaches >=10k rows.
    """
    rng = ctx.rng
    f = ctx.faker
    base_codes = ["5411", "5812", "5541", "4111", "7011", "4511", "5311", "5999", "4814", "8011",
                  "5651", "5732", "5912", "5942", "5944", "5945", "5947", "5965", "5970", "5994",
                  "6011", "6012", "6051", "7299", "7372", "7399", "7512", "7995", "8021", "8050"]
    base_desc = {
        "5411": "Grocery Stores", "5812": "Eating Places & Restaurants",
        "5541": "Service Stations", "4111": "Local Commuter Transport",
        "7011": "Lodging - Hotels", "4511": "Airlines", "5311": "Department Stores",
        "5999": "Misc Specialty Retail", "4814": "Telecom Services", "8011": "Doctors",
    }
    return pd.DataFrame(
        {
            "merchant_id": [f"MER{i:08d}" for i in range(1, n + 1)],
            "merchant_name": [f.company() for _ in range(n)],
            "mcc": rng.choice(base_codes, size=n),
            "description": [base_desc.get(c, "Other Merchant") for c in rng.choice(base_codes, size=n)],
            "category": weighted_choice(rng, ["Retail", "Food", "Travel", "Telecom", "Healthcare", "Other"], [0.30, 0.20, 0.15, 0.10, 0.10, 0.15], n),
            "country": rng.choice(country_codes(), size=n),
        }
    )


def _payment_instructions(ctx: GenContext, accounts: pd.DataFrame, n: int = 12_000) -> pd.DataFrame:
    rng = ctx.rng
    src = rng.choice(accounts["account_id"].to_numpy(), size=n)
    dst = rng.choice(accounts["account_id"].to_numpy(), size=n)
    return pd.DataFrame(
        {
            "instruction_id": [f"PIN{i:09d}" for i in range(1, n + 1)],
            "source_account_id": src,
            "dest_account_id": dst,
            "rail": weighted_choice(rng, ["card", "ach", "wire", "rtp", "sepa"], [0.55, 0.25, 0.05, 0.10, 0.05], n),
            "amount": lognormal_amounts(rng, n, mean=4.0, sigma=1.1),
            "currency": rng.choice(currency_codes(), size=n),
            "created_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
            "status": weighted_choice(rng, ["pending", "submitted", "completed", "rejected"], [0.05, 0.10, 0.80, 0.05], n),
        }
    )


def _payments(ctx: GenContext, instructions: pd.DataFrame, merchants: pd.DataFrame, n: int = 200_000) -> pd.DataFrame:
    rng = ctx.rng
    inst_completed = instructions[instructions["status"].isin(["completed", "submitted"])]
    inst_ids = rng.choice(inst_completed["instruction_id"].to_numpy(), size=n)
    auth_ts = daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30"))
    # latency hours: bimodal — most fast (<1h), tail to 72h
    fast = rng.normal(0.4, 0.25, size=n).clip(0.05, 12)
    slow = rng.normal(36, 12, size=n).clip(2, 96)
    pick_slow = rng.random(n) < 0.07
    latency_h = np.where(pick_slow, slow, fast)
    settlement_ts = auth_ts + pd.to_timedelta(latency_h, unit="h")
    rail = weighted_choice(rng, ["card", "ach", "wire", "rtp", "sepa"], [0.55, 0.25, 0.05, 0.10, 0.05], n)
    auth_failed = rng.random(n) < 0.06
    return pd.DataFrame(
        {
            "payment_id": [f"PAY{i:010d}" for i in range(1, n + 1)],
            "instruction_id": inst_ids,
            "rail": rail,
            "merchant_id": rng.choice(merchants["merchant_id"].to_numpy(), size=n),
            "mcc": rng.choice(merchants["mcc"].to_numpy(), size=n),
            "amount": lognormal_amounts(rng, n, mean=3.8, sigma=1.0),
            "currency": rng.choice(currency_codes(), size=n),
            "auth_ts": auth_ts,
            "settlement_ts": settlement_ts,
            "auth_status": np.where(auth_failed, "declined", "approved"),
            "is_stp": np.where(auth_failed, False, rng.random(n) < 0.92),
            "interchange_amount": np.round(rng.uniform(0.05, 1.8, size=n), 2),
            "country": rng.choice(country_codes(), size=n),
        }
    )


def _settlements(ctx: GenContext, payments: pd.DataFrame) -> pd.DataFrame:
    rng = ctx.rng
    approved = payments[payments["auth_status"] == "approved"].copy()
    n = len(approved)
    return pd.DataFrame(
        {
            "settlement_id": [f"STL{i:010d}" for i in range(1, n + 1)],
            "payment_id": approved["payment_id"].to_numpy(),
            "amount": approved["amount"].to_numpy(),
            "currency": approved["currency"].to_numpy(),
            "settled_at": approved["settlement_ts"].to_numpy(),
            "batch_id": [f"BTH{rng.integers(1, 5_000):05d}" for _ in range(n)],
            "fee_amount": np.round(approved["amount"].to_numpy() * rng.uniform(0.001, 0.029, size=n), 2),
            "network": weighted_choice(rng, ["VISA", "MC", "AMEX", "ACH", "SWIFT", "RTP"], [0.45, 0.30, 0.05, 0.12, 0.04, 0.04], n),
        }
    )


def _chargebacks(ctx: GenContext, payments: pd.DataFrame) -> pd.DataFrame:
    rng = ctx.rng
    card = payments[payments["rail"] == "card"]
    target = max(10_000, int(len(card) * 0.10))
    cb_idx = rng.choice(len(card), size=min(target, len(card)), replace=False)
    cb = card.iloc[cb_idx].copy().reset_index(drop=True)
    n = len(cb)
    return pd.DataFrame(
        {
            "chargeback_id": [f"CB{i:09d}" for i in range(1, n + 1)],
            "payment_id": cb["payment_id"].to_numpy(),
            "reason_code": weighted_choice(
                rng, ["10.4", "13.1", "13.2", "11.3", "12.6"], [0.30, 0.25, 0.20, 0.15, 0.10], n
            ),
            "amount": cb["amount"].to_numpy(),
            "filed_at": pd.to_datetime(cb["auth_ts"].to_numpy()) + pd.to_timedelta(rng.integers(1, 60, size=n), unit="D"),
            "status": weighted_choice(rng, ["open", "won", "lost"], [0.18, 0.42, 0.40], n),
        }
    )


def _disputes(ctx: GenContext, chargebacks: pd.DataFrame) -> pd.DataFrame:
    rng = ctx.rng
    disputed = chargebacks[chargebacks["status"].isin(["open", "won", "lost"])]
    n = max(10_000, len(disputed))
    if n > len(disputed):
        # supplement with non-card disputes (ACH returns etc.)
        extra = n - len(disputed)
        opened_at = daterange_minutes(rng, extra, pd.Timestamp("2024-02-01"), pd.Timestamp("2026-04-30"))
        df = pd.DataFrame(
            {
                "dispute_id": [f"DSP{i:09d}" for i in range(1, n + 1)],
                "chargeback_id": list(disputed["chargeback_id"].to_numpy()) + [None] * extra,
                "opened_ts": list(disputed["filed_at"].to_numpy()) + list(opened_at),
                "category": weighted_choice(
                    rng,
                    ["fraud", "non_receipt", "duplicate", "quality", "billing"],
                    [0.40, 0.25, 0.10, 0.15, 0.10],
                    n,
                ),
                "amount": list(disputed["amount"].to_numpy()) + list(lognormal_amounts(rng, extra, 4.0, 0.8)),
            }
        )
    else:
        df = pd.DataFrame(
            {
                "dispute_id": [f"DSP{i:09d}" for i in range(1, n + 1)],
                "chargeback_id": disputed["chargeback_id"].to_numpy()[:n],
                "opened_ts": disputed["filed_at"].to_numpy()[:n],
                "category": weighted_choice(
                    rng, ["fraud", "non_receipt", "duplicate", "quality", "billing"], [0.40, 0.25, 0.10, 0.15, 0.10], n
                ),
                "amount": disputed["amount"].to_numpy()[:n],
            }
        )
    res_days = rng.integers(1, 90, size=n)
    df["resolved_ts"] = pd.to_datetime(df["opened_ts"]) + pd.to_timedelta(res_days, unit="D")
    df["status"] = weighted_choice(rng, ["pending", "resolved_customer", "resolved_merchant"], [0.10, 0.55, 0.35], n)
    return df


def _fraud_alerts(ctx: GenContext, payments: pd.DataFrame, n: int = 10_000) -> pd.DataFrame:
    rng = ctx.rng
    pid = rng.choice(payments["payment_id"].to_numpy(), size=n)
    return pd.DataFrame(
        {
            "alert_id": [f"FRA{i:09d}" for i in range(1, n + 1)],
            "payment_id": pid,
            "score": np.round(rng.beta(2, 5, size=n), 4),
            "model_version": rng.choice(["v3.4", "v3.5", "v4.0", "v4.1"], size=n),
            "rule_set": weighted_choice(rng, ["velocity", "geo_mismatch", "device_change", "ml_only", "manual"], [0.30, 0.20, 0.15, 0.30, 0.05], n),
            "raised_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
            "outcome": weighted_choice(rng, ["true_positive", "false_positive", "review", "auto_block"], [0.18, 0.55, 0.20, 0.07], n),
        }
    )


def generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    ctx = make_context(seed)
    customers = _customers(ctx)
    accounts = _accounts(ctx, customers)
    merchants = _mcc_assignments(ctx)
    instructions = _payment_instructions(ctx, accounts)
    payments = _payments(ctx, instructions, merchants)
    settlements = _settlements(ctx, payments)
    chargebacks = _chargebacks(ctx, payments)
    disputes = _disputes(ctx, chargebacks)
    fraud_alerts = _fraud_alerts(ctx, payments)

    tables = {
        "customers": customers,
        "accounts": accounts,
        "merchants": merchants,
        "payment_instructions": instructions,
        "payments": payments,
        "settlements": settlements,
        "chargebacks": chargebacks,
        "disputes": disputes,
        "fraud_alerts": fraud_alerts,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
_payments(ctx, instructions, merchants)
    settlements = _settlements(ctx, payments)
    chargebacks = _chargebacks(ctx, payments)
    disputes = _disputes(ctx, chargebacks)
    fraud_alerts = _fraud_alerts(ctx, payments)

    tables = {
        "customers": customers,
        "accounts": accounts,
        "merchants": merchants,
        "payment_instructions": instructions,
        "payments": payments,
        "settlements": settlements,
        "chargebacks": chargebacks,
        "disputes": disputes,
        "fraud_alerts": fraud_alerts,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
