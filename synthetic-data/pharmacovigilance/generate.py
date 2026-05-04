"""
Synthetic Pharmacovigilance data.

Entities (>=8): products, patients, reporters, cases, adverse_events,
case_drugs, narratives, follow_ups, signals, regulatory_submissions.
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

SUBDOMAIN = "pharmacovigilance"


def _products(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "product_id": [f"DRG{i:06d}" for i in range(1, n + 1)],
        "tradename": [f"{f.last_name()}{rng.choice(['x', 'tin', 'ol', 'ase', 'ide', 'in'])}{i}" for i in range(n)],
        "inn": [f"{f.word()}-{rng.integers(100, 999)}-{i}" for i in range(n)],
        "atc_code": rng.choice(["A02", "A10", "B01", "C09", "J01", "L01", "M01", "N02", "N06", "R03"], size=n),
        "form": weighted_choice(rng, ["tablet", "capsule", "injection", "syrup", "patch", "inhaler"], [0.40, 0.25, 0.15, 0.10, 0.05, 0.05], n),
        "marketing_authorization_country": rng.choice(country_codes(), size=n),
        "approval_year": rng.integers(1990, 2026, size=n),
    })


def _patients(ctx, n=20_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "patient_id": [f"PT{i:08d}" for i in range(1, n + 1)],
        "age": rng.integers(0, 95, size=n),
        "sex": weighted_choice(rng, ["F", "M", "U"], [0.50, 0.48, 0.02], n),
        "weight_kg": np.round(rng.normal(75, 18, size=n).clip(2, 200), 1),
        "country": rng.choice(country_codes(), size=n),
        "pregnancy_status": weighted_choice(rng, ["NA", "no", "yes", "unknown"], [0.50, 0.40, 0.05, 0.05], n),
    })


def _reporters(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "reporter_id": [f"RPT{i:07d}" for i in range(1, n + 1)],
        "name": [f.name() for _ in range(n)],
        "role": weighted_choice(rng, ["physician", "pharmacist", "nurse", "consumer", "lawyer", "regulator"], [0.40, 0.20, 0.15, 0.20, 0.02, 0.03], n),
        "country": rng.choice(country_codes(), size=n),
        "qualified_hcp": rng.random(n) < 0.7,
    })


def _cases(ctx, patients, reporters, products, n=80_000):
    rng = ctx.rng
    return pd.DataFrame({
        "case_id": [f"PV{i:09d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "reporter_id": rng.choice(reporters["reporter_id"].to_numpy(), size=n),
        "primary_product_id": rng.choice(products["product_id"].to_numpy(), size=n),
        "received_at": daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30")),
        "seriousness": weighted_choice(rng, ["non_serious", "serious", "life_threatening", "death"], [0.65, 0.27, 0.05, 0.03], n),
        "expectedness": weighted_choice(rng, ["expected", "unexpected"], [0.70, 0.30], n),
        "case_status": weighted_choice(rng, ["open", "submitted", "closed_followup", "closed"], [0.10, 0.15, 0.20, 0.55], n),
        "country": rng.choice(country_codes(), size=n),
    })


def _adverse_events(ctx, cases, n_target=120_000):
    rng = ctx.rng
    counts = rng.integers(1, 4, size=len(cases))
    case_ids = np.repeat(cases["case_id"].to_numpy(), counts)
    n = max(n_target, len(case_ids))
    if n > len(case_ids):
        case_ids = np.concatenate([case_ids, rng.choice(cases["case_id"].to_numpy(), size=n - len(case_ids))])
    return pd.DataFrame({
        "ae_id": [f"AE{i:09d}" for i in range(1, n + 1)],
        "case_id": case_ids,
        "meddra_pt": rng.choice(["Headache", "Nausea", "Rash", "Dizziness", "Hypotension", "Tachycardia", "Insomnia", "Pruritus", "Vomiting", "Anxiety", "Hepatotoxicity"], size=n),
        "outcome": weighted_choice(rng, ["recovered", "recovering", "fatal", "ongoing", "unknown"], [0.55, 0.20, 0.02, 0.18, 0.05], n),
        "onset_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2022-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
    })


def _case_drugs(ctx, cases, products, n_target=120_000):
    rng = ctx.rng
    n = n_target
    return pd.DataFrame({
        "case_drug_id": [f"CDR{i:09d}" for i in range(1, n + 1)],
        "case_id": rng.choice(cases["case_id"].to_numpy(), size=n),
        "product_id": rng.choice(products["product_id"].to_numpy(), size=n),
        "role": weighted_choice(rng, ["suspect", "concomitant", "interacting", "treatment"], [0.55, 0.30, 0.05, 0.10], n),
        "dose_text": rng.choice(["10 mg/day", "20 mg/day", "50 mg/day", "100 mg/day", "1 tab BID", "5 mL TID"], size=n),
        "indication": rng.choice(["Hypertension", "Diabetes", "Asthma", "Depression", "Pain", "Infection"], size=n),
    })


def _narratives(ctx, cases, n_min=10_000):
    rng = ctx.rng
    n = max(n_min, len(cases))
    n = min(n, len(cases))
    sub = cases.sample(n=n, random_state=ctx.seed)
    return pd.DataFrame({
        "narrative_id": [f"NAR{i:09d}" for i in range(1, n + 1)],
        "case_id": sub["case_id"].to_numpy(),
        "language": weighted_choice(rng, ["en", "es", "fr", "de", "ja", "zh"], [0.55, 0.10, 0.10, 0.10, 0.05, 0.10], n),
        "length_words": rng.integers(40, 1500, size=n),
        "version": rng.integers(1, 5, size=n),
    })


def _followups(ctx, cases, n=20_000):
    rng = ctx.rng
    return pd.DataFrame({
        "followup_id": [f"FU{i:08d}" for i in range(1, n + 1)],
        "case_id": rng.choice(cases["case_id"].to_numpy(), size=n),
        "received_at": daterange_minutes(rng, n, pd.Timestamp("2022-02-01"), pd.Timestamp("2026-04-30")),
        "type": weighted_choice(rng, ["clarification", "outcome_update", "additional_event", "withdrawal"], [0.45, 0.35, 0.15, 0.05], n),
        "completeness_score": np.round(rng.beta(5, 2, size=n), 3),
    })


def _signals(ctx, products, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "signal_id": [f"SIG{i:07d}" for i in range(1, n + 1)],
        "product_id": rng.choice(products["product_id"].to_numpy(), size=n),
        "meddra_pt": rng.choice(["Hepatotoxicity", "QT Prolongation", "Stevens-Johnson", "Agranulocytosis", "Anaphylaxis", "Suicidal Ideation", "Renal Failure"], size=n),
        "detected_at": daterange_minutes(rng, n, pd.Timestamp("2023-01-01"), pd.Timestamp("2026-04-30")),
        "method": weighted_choice(rng, ["disproportionality", "literature", "manual_review", "machine_learning", "regulator_query"], [0.40, 0.20, 0.15, 0.20, 0.05], n),
        "status": weighted_choice(rng, ["under_review", "validated", "refuted", "monitoring"], [0.30, 0.30, 0.20, 0.20], n),
    })


def _regulatory_submissions(ctx, cases, n=15_000):
    rng = ctx.rng
    return pd.DataFrame({
        "submission_id": [f"REG{i:08d}" for i in range(1, n + 1)],
        "case_id": rng.choice(cases["case_id"].to_numpy(), size=n),
        "agency": weighted_choice(rng, ["FDA", "EMA", "PMDA", "MHRA", "TGA", "Health Canada"], [0.40, 0.30, 0.10, 0.08, 0.05, 0.07], n),
        "format": weighted_choice(rng, ["E2B(R3)", "E2B(R2)", "PDF", "PSUR"], [0.55, 0.20, 0.15, 0.10], n),
        "submitted_at": daterange_minutes(rng, n, pd.Timestamp("2022-02-01"), pd.Timestamp("2026-04-30")),
        "ack_status": weighted_choice(rng, ["accepted", "rejected", "pending"], [0.85, 0.05, 0.10], n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    products = _products(ctx)
    patients = _patients(ctx)
    reporters = _reporters(ctx)
    cases = _cases(ctx, patients, reporters, products)
    aes = _adverse_events(ctx, cases)
    cdrugs = _case_drugs(ctx, cases, products)
    narr = _narratives(ctx, cases)
    fu = _followups(ctx, cases)
    signals = _signals(ctx, products)
    regs = _regulatory_submissions(ctx, cases)
    tables = {
        "products": products,
        "patients": patients,
        "reporters": reporters,
        "cases": cases,
        "adverse_events": aes,
        "case_drugs": cdrugs,
        "narratives": narr,
        "follow_ups": fu,
        "signals": signals,
        "regulatory_submissions": regs,
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
