"""
Synthetic Tax Administration data — IRS MeF + OECD CRS / FATCA.

Entities (>=8): taxpayer, return, form, schedule, transmission,
acknowledgement, audit, fatca_account, withholding, payment.

Realism:
  - Form types: 1040, 1040-SR, 1120, 1120-S, 1065 (US federal).
  - MeF transmission cycle: e-file -> ack within seconds-to-minutes.
  - CRS/FATCA accounts use TIN format and reportable jurisdiction codes.
  - AGI distribution lognormal, weighted toward middle income.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    daterange_minutes,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "tax_administration"

FORM_TYPES = [
    ("1040", "U.S. Individual Income Tax Return", "individual"),
    ("1040-SR", "U.S. Tax Return for Seniors", "individual"),
    ("1040X", "Amended U.S. Individual Income Tax Return", "individual"),
    ("1120", "U.S. Corporation Income Tax Return", "corporate"),
    ("1120-S", "U.S. Income Tax Return for an S Corporation", "corporate"),
    ("1065", "U.S. Return of Partnership Income", "partnership"),
    ("990", "Return of Organization Exempt From Income Tax", "exempt"),
    ("941", "Employer's Quarterly Federal Tax Return", "employment"),
]

SCHEDULES = ["Schedule A", "Schedule B", "Schedule C", "Schedule D", "Schedule E",
             "Schedule SE", "Schedule K-1", "Form 1099-MISC", "Form 1099-INT",
             "Form 1099-DIV", "Form W-2", "Form 8606", "Form 8949"]


def _taxpayers(ctx, n=15_000):
    rng = ctx.rng
    f = ctx.faker
    is_business = rng.random(n) < 0.18
    return pd.DataFrame({
        "taxpayer_id": [f"TP{i:09d}" for i in range(1, n + 1)],
        "tin_hash": [f"sha256-{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "tin_type": np.where(is_business, weighted_choice(rng, ["EIN"], [1.0], n), weighted_choice(rng, ["SSN", "ITIN"], [0.97, 0.03], n)),
        "filing_entity_type": np.where(is_business, weighted_choice(rng, ["C-Corp", "S-Corp", "LLC", "Partnership", "Sole-Proprietor"], [0.20, 0.25, 0.30, 0.15, 0.10], n), "Individual"),
        "legal_name": [f.company() if is_business[i] else f.name() for i in range(n)],
        "address_line": [f.street_address() for _ in range(n)],
        "address_city": [f.city() for _ in range(n)],
        "address_state": rng.choice(["CA", "NY", "TX", "FL", "IL", "PA", "OH", "MA", "WA", "GA", "NJ", "VA", "NC", "MI", "AZ"], size=n),
        "address_country": "US",
        "filing_status": weighted_choice(rng, ["single", "married_joint", "married_separate", "head_of_household", "qualifying_widow"], [0.42, 0.40, 0.04, 0.13, 0.01], n),
        "registered_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2010-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s").date,
        "active": rng.random(n) < 0.96,
    })


def _returns(ctx, taxpayers, n=80_000):
    """Primary entity — tax returns."""
    rng = ctx.rng
    tax_year = rng.choice([2022, 2023, 2024, 2025], size=n, p=[0.18, 0.27, 0.30, 0.25])
    filed = pd.to_datetime(np.array([pd.Timestamp(f"{y + 1}-04-15").timestamp() for y in tax_year]) + rng.integers(-90, 200, size=n) * 86400, unit="s")
    form_idx = rng.integers(0, len(FORM_TYPES), size=n)
    form_type = [FORM_TYPES[i][0] for i in form_idx]
    agi = np.round(rng.lognormal(mean=10.7, sigma=0.85, size=n), 2)
    total_tax = np.round(agi * rng.uniform(0.05, 0.32, size=n), 2)
    withheld = np.round(total_tax * rng.uniform(0.5, 1.3, size=n), 2)
    refund_or_due = withheld - total_tax
    return pd.DataFrame({
        "return_id": [f"RTN{i:010d}" for i in range(1, n + 1)],
        "taxpayer_id": rng.choice(taxpayers["taxpayer_id"].to_numpy(), size=n),
        "tax_year": tax_year,
        "form_type": form_type,
        "filing_status": weighted_choice(rng, ["single", "married_joint", "married_separate", "head_of_household"], [0.40, 0.42, 0.05, 0.13], n),
        "submission_id": [f"M{rng.integers(10**10, 10**11):011d}" for _ in range(n)],
        "filed_at": filed,
        "due_date": pd.to_datetime([f"{y + 1}-04-15" for y in tax_year]).date,
        "is_amended": rng.random(n) < 0.03,
        "is_extension": rng.random(n) < 0.10,
        "agi": agi,
        "total_income": np.round(agi * rng.uniform(0.95, 1.10, size=n), 2),
        "taxable_income": np.round(agi * rng.uniform(0.65, 1.0, size=n), 2),
        "total_tax": total_tax,
        "total_payments": withheld,
        "refund_amount": np.where(refund_or_due > 0, refund_or_due, 0).round(2),
        "balance_due": np.where(refund_or_due < 0, -refund_or_due, 0).round(2),
        "filing_method": weighted_choice(rng, ["e-file", "paper", "preparer-efile"], [0.70, 0.10, 0.20], n),
        "status": weighted_choice(rng, ["accepted", "rejected", "processing", "amended"], [0.86, 0.06, 0.05, 0.03], n),
    })


def _forms(ctx, returns, n_target=200_000):
    rng = ctx.rng
    n_per = max(2, n_target // len(returns))
    n = n_per * len(returns)
    return_id = np.repeat(returns["return_id"].to_numpy(), n_per)
    form_idx = rng.integers(0, len(FORM_TYPES), size=n)
    return pd.DataFrame({
        "form_id": [f"FRM{i:010d}" for i in range(1, n + 1)],
        "return_id": return_id,
        "form_code": [FORM_TYPES[i][0] for i in form_idx],
        "form_description": [FORM_TYPES[i][1] for i in form_idx],
        "form_revision": rng.choice(["2022-12", "2023-11", "2024-10"], size=n),
        "is_primary": np.tile(np.arange(n_per) == 0, len(returns)),
        "page_count": rng.integers(1, 20, size=n),
    })


def _schedules(ctx, returns, n_target=160_000):
    rng = ctx.rng
    n = min(n_target, len(returns) * 4)
    return pd.DataFrame({
        "schedule_id": [f"SCH{i:010d}" for i in range(1, n + 1)],
        "return_id": rng.choice(returns["return_id"].to_numpy(), size=n),
        "schedule_code": rng.choice(SCHEDULES, size=n),
        "line_count": rng.integers(1, 50, size=n),
        "total_amount": np.round(rng.lognormal(mean=8, sigma=2, size=n), 2),
    })


def _transmissions(ctx, returns, n_target=80_000):
    """MeF transmissions — efile bundle envelope."""
    rng = ctx.rng
    n = min(n_target, len(returns))
    sub = returns.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    sent_ts = pd.to_datetime(sub["filed_at"].to_numpy())
    return pd.DataFrame({
        "transmission_id": [f"TRX{i:010d}" for i in range(1, n + 1)],
        "submission_id": sub["submission_id"].to_numpy(),
        "return_id": sub["return_id"].to_numpy(),
        "ero_id": [f"ERO{rng.integers(10**5, 10**6):06d}" for _ in range(n)],
        "transmitter_id": [f"TXM{rng.integers(10**4, 10**5):05d}" for _ in range(n)],
        "sent_at": sent_ts,
        "received_at": sent_ts + pd.to_timedelta(rng.integers(1, 60, size=n), unit="s"),
        "envelope_format": weighted_choice(rng, ["MeF-XML", "MeF-XML-2.0", "Paper-Image"], [0.78, 0.20, 0.02], n),
        "byte_size": rng.integers(2_000, 5_000_000, size=n),
        "transmission_status": weighted_choice(rng, ["received", "validated", "rejected", "queued"], [0.05, 0.85, 0.05, 0.05], n),
    })


def _acknowledgements(ctx, transmissions, n_target=80_000):
    rng = ctx.rng
    n = min(n_target, len(transmissions))
    src = transmissions.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    received = pd.to_datetime(src["received_at"].to_numpy())
    ack_ts = received + pd.to_timedelta(rng.integers(2, 600, size=n), unit="s")
    return pd.DataFrame({
        "ack_id": [f"ACK{i:010d}" for i in range(1, n + 1)],
        "transmission_id": src["transmission_id"].to_numpy(),
        "submission_id": src["submission_id"].to_numpy(),
        "ack_status": weighted_choice(rng, ["A", "R", "T", "E"], [0.85, 0.10, 0.04, 0.01], n),
        "ack_ts": ack_ts,
        "error_codes": np.where(rng.random(n) < 0.10, rng.choice(["F1040-001", "F1040-008", "SEIC-F1040-501-02", "F8606-001"], size=n), None),
        "error_message": np.where(rng.random(n) < 0.10, rng.choice(["Invalid SSN", "Duplicate filing", "Missing schedule", "AGI mismatch"], size=n), None),
    })


def _audits(ctx, returns, n=10_000):
    rng = ctx.rng
    opened = pd.to_datetime(rng.integers(int(pd.Timestamp("2023-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "audit_id": [f"AUD{i:08d}" for i in range(1, n + 1)],
        "return_id": rng.choice(returns["return_id"].to_numpy(), size=n),
        "audit_type": weighted_choice(rng, ["correspondence", "office", "field", "tcmp"], [0.78, 0.13, 0.07, 0.02], n),
        "selection_reason": weighted_choice(rng, ["DIF-score", "random", "informant", "computer-match", "third-party-info", "related"], [0.55, 0.10, 0.05, 0.20, 0.05, 0.05], n),
        "opened_at": opened,
        "closed_at": opened + pd.to_timedelta(rng.integers(30, 720, size=n), unit="D"),
        "examiner_id": [f"EXM{rng.integers(10**4, 10**5):05d}" for _ in range(n)],
        "proposed_adjustment": np.round(rng.lognormal(mean=8, sigma=1.6, size=n) * np.where(rng.random(n) < 0.5, 1, -1), 2),
        "outcome": weighted_choice(rng, ["no_change", "agreed_change", "appealed", "tax_court", "open"], [0.40, 0.45, 0.05, 0.05, 0.05], n),
    })


def _fatca_accounts(ctx, taxpayers, n=20_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "fatca_account_id": [f"FATCA{i:08d}" for i in range(1, n + 1)],
        "taxpayer_id": rng.choice(taxpayers["taxpayer_id"].to_numpy(), size=n),
        "account_holder_name": [f.name() for _ in range(n)],
        "reporting_country": rng.choice(["US"], size=n),
        "host_country": rng.choice(["CH", "LU", "KY", "BM", "VG", "GB", "SG", "HK", "AU", "CA", "DE", "JP"], size=n),
        "financial_institution_giin": [f"{rng.integers(10**5, 10**6):06d}.99999.SL.{rng.choice(['CHE', 'LUX', 'CYM', 'BMU'])}" for _ in range(n)],
        "account_balance_usd": np.round(rng.lognormal(mean=11, sigma=1.7, size=n), 2),
        "currency": rng.choice(["USD", "EUR", "GBP", "CHF", "JPY"], size=n, p=[0.40, 0.25, 0.10, 0.15, 0.10]),
        "report_year": rng.choice([2022, 2023, 2024, 2025], size=n),
        "reportable_under": weighted_choice(rng, ["FATCA", "CRS", "Both"], [0.30, 0.40, 0.30], n),
        "is_recalcitrant": rng.random(n) < 0.04,
    })


def _withholding(ctx, taxpayers, n=40_000):
    rng = ctx.rng
    return pd.DataFrame({
        "withholding_id": [f"WHL{i:09d}" for i in range(1, n + 1)],
        "taxpayer_id": rng.choice(taxpayers["taxpayer_id"].to_numpy(), size=n),
        "year": rng.choice([2022, 2023, 2024, 2025], size=n),
        "income_type": weighted_choice(rng, ["wages", "interest", "dividends", "rents", "royalties", "1099-NEC", "1099-MISC"], [0.55, 0.10, 0.10, 0.05, 0.02, 0.10, 0.08], n),
        "gross_amount": np.round(rng.lognormal(mean=9, sigma=1.2, size=n), 2),
        "withheld_amount": np.round(rng.lognormal(mean=7.5, sigma=1.0, size=n), 2),
        "payer_ein": [f"{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "form_received": weighted_choice(rng, ["W-2", "1099-INT", "1099-DIV", "1099-NEC", "1099-MISC", "1099-R"], [0.55, 0.10, 0.10, 0.10, 0.08, 0.07], n),
    })


def _payments(ctx, returns, n=30_000):
    rng = ctx.rng
    paid_at = daterange_minutes(rng, n, pd.Timestamp("2023-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "payment_id": [f"PMT{i:09d}" for i in range(1, n + 1)],
        "return_id": rng.choice(returns["return_id"].to_numpy(), size=n),
        "payment_method": weighted_choice(rng, ["EFTPS", "Direct-Pay", "ACH", "credit_card", "check", "money_order"], [0.30, 0.20, 0.20, 0.15, 0.10, 0.05], n),
        "amount": np.round(rng.lognormal(mean=7, sigma=1.2, size=n), 2),
        "paid_at": paid_at,
        "applied_to_year": rng.choice([2022, 2023, 2024, 2025], size=n),
        "designated_as": weighted_choice(rng, ["balance_due", "estimated_tax", "extension", "penalty", "interest"], [0.55, 0.30, 0.05, 0.05, 0.05], n),
        "status": weighted_choice(rng, ["posted", "pending", "returned", "refunded"], [0.92, 0.05, 0.02, 0.01], n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    taxpayers = _taxpayers(ctx)
    returns = _returns(ctx, taxpayers)
    forms = _forms(ctx, returns)
    schedules = _schedules(ctx, returns)
    transmissions = _transmissions(ctx, returns)
    acks = _acknowledgements(ctx, transmissions)
    audits = _audits(ctx, returns)
    fatca = _fatca_accounts(ctx, taxpayers)
    withholding = _withholding(ctx, taxpayers)
    payments = _payments(ctx, returns)
    tables = {
        "taxpayer": taxpayers,
        "return": returns,
        "form": forms,
        "schedule": schedules,
        "transmission": transmissions,
        "acknowledgement": acks,
        "audit": audits,
        "fatca_account": fatca,
        "withholding": withholding,
        "payment": payments,
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
