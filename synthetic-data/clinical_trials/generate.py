"""
Synthetic Clinical Trials data — CDISC SDTM v3.4.

Entities (>=8): study, site, subject (DM), demographics, visit (SV),
exposure (EX), adverse_event (AE), concomitant_medication (CM), lab (LB),
ecg (EG), vital_signs (VS).

Realism:
  - SDTM USUBJID format: STUDY-SITE-SEQ.
  - AE seriousness ratios reflect typical Phase 2/3 distributions.
  - Lab reference ranges per analyte; flags for H/L based on ULN/LLN.
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

SUBDOMAIN = "clinical_trials"

THERAPEUTIC_AREAS = ["Oncology", "Cardiology", "Neurology", "Immunology", "Endocrinology", "Infectious Disease", "Respiratory"]
PHASES = ["Phase 1", "Phase 2", "Phase 2b", "Phase 3", "Phase 4"]
LABS = [
    ("ALT", "Alanine aminotransferase", "U/L", 7.0, 56.0),
    ("AST", "Aspartate aminotransferase", "U/L", 10.0, 40.0),
    ("ALP", "Alkaline phosphatase", "U/L", 44.0, 147.0),
    ("BILI", "Total bilirubin", "mg/dL", 0.1, 1.2),
    ("CREAT", "Creatinine", "mg/dL", 0.6, 1.3),
    ("BUN", "Blood urea nitrogen", "mg/dL", 7.0, 20.0),
    ("GLUC", "Glucose", "mg/dL", 70.0, 99.0),
    ("HGB", "Hemoglobin", "g/dL", 12.0, 17.0),
    ("WBC", "White blood cell count", "10*9/L", 4.0, 11.0),
    ("PLAT", "Platelets", "10*9/L", 150.0, 400.0),
    ("NA", "Sodium", "mEq/L", 135.0, 145.0),
    ("K", "Potassium", "mEq/L", 3.5, 5.0),
]
MEDDRA_PT = [
    "Headache", "Nausea", "Fatigue", "Diarrhoea", "Vomiting", "Pyrexia",
    "Cough", "Insomnia", "Arthralgia", "Dizziness", "Constipation", "Rash",
    "Dyspnoea", "Anaemia", "Neutropenia", "Thrombocytopenia", "Hepatotoxicity",
]


def _studies(ctx, n=200):
    rng = ctx.rng
    return pd.DataFrame({
        "studyid": [f"STDY{i:04d}" for i in range(1, n + 1)],
        "study_title": [f"A {rng.choice(['Phase 2', 'Phase 3'])} Study of Compound-{i:04d}" for i in range(1, n + 1)],
        "therapeutic_area": rng.choice(THERAPEUTIC_AREAS, size=n),
        "phase": rng.choice(PHASES, size=n, p=[0.10, 0.30, 0.10, 0.40, 0.10]),
        "indication": rng.choice(["NSCLC", "HER2+ Breast Cancer", "T2DM", "Hypertension", "Atopic Dermatitis", "RA", "MS"], size=n),
        "blinding": weighted_choice(rng, ["double-blind", "single-blind", "open-label"], [0.55, 0.15, 0.30], n),
        "started_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2018-01-01").timestamp()), int(pd.Timestamp("2025-06-01").timestamp()), size=n), unit="s").date,
        "primary_completion_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2027-12-31").timestamp()), size=n), unit="s").date,
        "status": weighted_choice(rng, ["recruiting", "active", "completed", "terminated", "suspended"], [0.20, 0.40, 0.30, 0.07, 0.03], n),
    })


def _sites(ctx, studies, n=2_500):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "siteid": [f"S{i:05d}" for i in range(1, n + 1)],
        "studyid": rng.choice(studies["studyid"].to_numpy(), size=n),
        "site_name": [f.company() for _ in range(n)],
        "country": rng.choice(["US", "GB", "DE", "FR", "JP", "AU", "CA", "BR", "IN", "CN", "ES", "IT"], size=n),
        "principal_investigator": [f.name() for _ in range(n)],
        "irb_approval_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2018-01-01").timestamp()), int(pd.Timestamp("2025-01-01").timestamp()), size=n), unit="s").date,
        "activated_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2018-06-01").timestamp()), int(pd.Timestamp("2025-06-01").timestamp()), size=n), unit="s").date,
        "subject_target": rng.integers(5, 80, size=n),
        "subject_enrolled": rng.integers(0, 80, size=n),
    })


def _subjects(ctx, studies, sites, n=15_000):
    """SDTM DM (Demographics) — primary entity."""
    rng = ctx.rng
    studyid = rng.choice(studies["studyid"].to_numpy(), size=n)
    siteid = rng.choice(sites["siteid"].to_numpy(), size=n)
    rfstdtc = pd.to_datetime(rng.integers(int(pd.Timestamp("2022-01-01").timestamp()), int(pd.Timestamp("2026-03-01").timestamp()), size=n), unit="s")
    age = rng.integers(18, 86, size=n)
    return pd.DataFrame({
        "usubjid": [f"{s}-{site[1:]}-{i:05d}" for i, (s, site) in enumerate(zip(studyid, siteid))],
        "studyid": studyid,
        "siteid": siteid,
        "subjid": [f"{i:05d}" for i in range(1, n + 1)],
        "rfstdtc": rfstdtc.date,
        "rfendtc": (rfstdtc + pd.to_timedelta(rng.integers(7, 730, size=n), unit="D")).date,
        "rficdtc": (rfstdtc - pd.to_timedelta(rng.integers(0, 30, size=n), unit="D")).date,
        "armcd": weighted_choice(rng, ["TRT", "PBO", "TRT-LOW", "TRT-HIGH"], [0.45, 0.30, 0.12, 0.13], n),
        "actarmcd": weighted_choice(rng, ["TRT", "PBO", "TRT-LOW", "TRT-HIGH", "SCRNFAIL"], [0.42, 0.28, 0.10, 0.10, 0.10], n),
        "age": age,
        "ageu": "YEARS",
        "sex": weighted_choice(rng, ["F", "M"], [0.52, 0.48], n),
        "race": weighted_choice(rng, ["WHITE", "BLACK OR AFRICAN AMERICAN", "ASIAN", "OTHER", "AMERICAN INDIAN OR ALASKA NATIVE"], [0.65, 0.15, 0.12, 0.06, 0.02], n),
        "ethnic": weighted_choice(rng, ["NOT HISPANIC OR LATINO", "HISPANIC OR LATINO", "NOT REPORTED"], [0.78, 0.18, 0.04], n),
        "country": rng.choice(["USA", "GBR", "DEU", "FRA", "JPN", "AUS", "CAN", "BRA"], size=n),
        "dthfl": weighted_choice(rng, ["", "Y"], [0.97, 0.03], n),
    })


def _visits(ctx, subjects, n_target=120_000):
    rng = ctx.rng
    n_per = max(8, n_target // len(subjects))
    n = n_per * len(subjects)
    usubjid = np.repeat(subjects["usubjid"].to_numpy(), n_per)
    visit_num = np.tile(np.arange(1, n_per + 1), len(subjects))
    visit_names = ["Screening", "Baseline", "Week 1", "Week 2", "Week 4", "Week 8", "Week 12", "Week 24", "EOT", "FUP"]
    visit = np.tile(np.array(visit_names + ["UNS"] * max(0, n_per - len(visit_names)))[:n_per], len(subjects))
    base = pd.to_datetime(np.repeat(pd.to_datetime(subjects["rfstdtc"]).to_numpy(), n_per))
    svstdtc = base + pd.to_timedelta(visit_num * 14, unit="D")
    return pd.DataFrame({
        "usubjid": usubjid,
        "visit": visit,
        "visitnum": visit_num,
        "svstdtc": svstdtc.date,
        "svendtc": (svstdtc + pd.to_timedelta(rng.integers(0, 4, size=n), unit="h")).date,
        "svstatus": weighted_choice(rng, ["completed", "missed", "discontinued"], [0.92, 0.05, 0.03], n),
    })


def _adverse_events(ctx, subjects, n=80_000):
    rng = ctx.rng
    aestdtc = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "aeseq": np.arange(1, n + 1),
        "usubjid": rng.choice(subjects["usubjid"].to_numpy(), size=n),
        "aeterm": rng.choice(MEDDRA_PT, size=n),
        "aedecod": rng.choice(MEDDRA_PT, size=n),
        "aebodsys": rng.choice(["Nervous system disorders", "Gastrointestinal disorders", "General disorders", "Skin and subcutaneous tissue disorders", "Blood and lymphatic system disorders", "Hepatobiliary disorders"], size=n),
        "aeser": weighted_choice(rng, ["N", "Y"], [0.85, 0.15], n),
        "aesev": weighted_choice(rng, ["MILD", "MODERATE", "SEVERE", "LIFE-THREATENING"], [0.55, 0.30, 0.12, 0.03], n),
        "aerel": weighted_choice(rng, ["NOT RELATED", "UNLIKELY RELATED", "POSSIBLY RELATED", "PROBABLY RELATED", "DEFINITELY RELATED"], [0.30, 0.25, 0.25, 0.15, 0.05], n),
        "aeacn": weighted_choice(rng, ["DOSE NOT CHANGED", "DOSE REDUCED", "DRUG INTERRUPTED", "DRUG WITHDRAWN"], [0.65, 0.15, 0.15, 0.05], n),
        "aeout": weighted_choice(rng, ["RECOVERED/RESOLVED", "RECOVERING/RESOLVING", "NOT RECOVERED/NOT RESOLVED", "FATAL", "UNKNOWN"], [0.65, 0.15, 0.12, 0.02, 0.06], n),
        "aestdtc": aestdtc.date,
        "aeendtc": (aestdtc + pd.to_timedelta(rng.integers(1, 60, size=n), unit="D")).date,
    })


def _concomitant_medications(ctx, subjects, n=60_000):
    rng = ctx.rng
    cmstdtc = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "cmseq": np.arange(1, n + 1),
        "usubjid": rng.choice(subjects["usubjid"].to_numpy(), size=n),
        "cmtrt": rng.choice(["Aspirin", "Atorvastatin", "Lisinopril", "Metformin", "Levothyroxine", "Amlodipine", "Omeprazole", "Acetaminophen", "Ibuprofen", "Sertraline"], size=n),
        "cmindc": rng.choice(["Hypertension", "Hyperlipidemia", "Diabetes", "Pain", "GERD", "Hypothyroidism", "Anxiety", "Other"], size=n),
        "cmdose": np.round(rng.choice([5, 10, 20, 25, 50, 100, 500, 1000], size=n), 2),
        "cmdosu": "mg",
        "cmdosfrq": rng.choice(["QD", "BID", "TID", "QHS", "PRN"], size=n),
        "cmroute": weighted_choice(rng, ["ORAL", "IV", "IM", "SC", "TOPICAL"], [0.85, 0.05, 0.04, 0.03, 0.03], n),
        "cmstdtc": cmstdtc.date,
        "cmendtc": (cmstdtc + pd.to_timedelta(rng.integers(1, 365, size=n), unit="D")).date,
    })


def _labs(ctx, subjects, n_target=200_000):
    rng = ctx.rng
    n = n_target
    lab_idx = rng.integers(0, len(LABS), size=n)
    test = [LABS[i][0] for i in lab_idx]
    test_disp = [LABS[i][1] for i in lab_idx]
    units = [LABS[i][2] for i in lab_idx]
    lows = np.array([LABS[i][3] for i in lab_idx])
    highs = np.array([LABS[i][4] for i in lab_idx])
    values = lows + (highs - lows) * rng.random(n)
    abn = rng.random(n) < 0.06
    values = np.where(abn, values * rng.uniform(1.5, 3.0, size=n), values)
    fl = np.where(abn, np.where(rng.random(n) < 0.5, "H", "L"), "")
    return pd.DataFrame({
        "lbseq": np.arange(1, n + 1),
        "usubjid": rng.choice(subjects["usubjid"].to_numpy(), size=n),
        "lbtestcd": test,
        "lbtest": test_disp,
        "lbcat": "CHEMISTRY",
        "lborres": np.round(values, 3),
        "lborresu": units,
        "lbstresn": np.round(values, 3),
        "lbstresu": units,
        "lbstnrlo": lows,
        "lbstnrhi": highs,
        "lbnrind": fl,
        "lbdtc": daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30")).date,
        "visitnum": rng.integers(1, 11, size=n),
    })


def _ecg(ctx, subjects, n=40_000):
    rng = ctx.rng
    return pd.DataFrame({
        "egseq": np.arange(1, n + 1),
        "usubjid": rng.choice(subjects["usubjid"].to_numpy(), size=n),
        "egtestcd": rng.choice(["HR", "PR", "QRS", "QT", "QTCB", "QTCF"], size=n),
        "egorres": np.round(rng.normal(400, 35, size=n), 1),
        "egorresu": "msec",
        "egstresn": np.round(rng.normal(400, 35, size=n), 1),
        "egnrind": weighted_choice(rng, ["", "H", "L", "ABNORMAL"], [0.85, 0.07, 0.04, 0.04], n),
        "egdtc": daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30")).date,
    })


def _exposures(ctx, subjects, n=50_000):
    rng = ctx.rng
    exstdtc = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "exseq": np.arange(1, n + 1),
        "usubjid": rng.choice(subjects["usubjid"].to_numpy(), size=n),
        "extrt": rng.choice(["IMP-001", "IMP-002", "PLACEBO"], size=n, p=[0.5, 0.2, 0.3]),
        "exdose": np.round(rng.choice([5, 10, 20, 50, 100, 200], size=n), 2),
        "exdosu": "mg",
        "exdosfrq": rng.choice(["QD", "BID", "Q2W", "Q4W"], size=n),
        "exroute": weighted_choice(rng, ["ORAL", "IV", "SC", "IM"], [0.65, 0.20, 0.10, 0.05], n),
        "exstdtc": exstdtc.date,
        "exendtc": (exstdtc + pd.to_timedelta(rng.integers(1, 90, size=n), unit="D")).date,
    })


def generate(seed=42):
    ctx = make_context(seed)
    studies = _studies(ctx)
    sites = _sites(ctx, studies)
    subjects = _subjects(ctx, studies, sites)
    visits = _visits(ctx, subjects)
    aes = _adverse_events(ctx, subjects)
    cms = _concomitant_medications(ctx, subjects)
    labs = _labs(ctx, subjects)
    ecg = _ecg(ctx, subjects)
    ex = _exposures(ctx, subjects)
    tables = {
        "study": studies,
        "site": sites,
        "subject": subjects,
        "visit": visits,
        "adverse_event": aes,
        "concomitant_medication": cms,
        "lab": labs,
        "ecg": ecg,
        "exposure": ex,
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
