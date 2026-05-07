"""
Synthetic Real-World Evidence data — OMOP CDM v5.4 (OHDSI).

Entities (>=8): person, observation_period, visit_occurrence, condition_occurrence,
drug_exposure, procedure_occurrence, measurement, concept, cohort, cohort_attribute.

Realism:
  - concept_id values are realistic OHDSI concept IDs (SNOMED branch: 4xxxxx,
    LOINC: 30xxxxxx, RxNorm: 19xxxxxx, ICD10CM: 35xxxxxxx).
  - Standard OMOP datatypes: condition_status_concept_id, type_concept_id,
    visit_concept_id (9201 Inpatient, 9202 Outpatient, 9203 ER).
  - Measurement: includes value_as_number + units_concept_id.
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

SUBDOMAIN = "real_world_evidence"


# Real OMOP CDM standard concept IDs.
GENDER_CONCEPTS = {"FEMALE": 8532, "MALE": 8507, "UNKNOWN": 0}
RACE_CONCEPTS = {"WHITE": 8527, "BLACK": 8516, "ASIAN": 8515, "OTHER": 8522, "UNKNOWN": 0}
VISIT_CONCEPTS = [9201, 9202, 9203, 9238, 581477]  # Inpatient, Outpatient, ER, Pharmacy, Office Visit
CONDITION_CONCEPTS = [
    (201826, "Type 2 diabetes mellitus", "SNOMED"),
    (320128, "Essential hypertension", "SNOMED"),
    (317009, "Asthma", "SNOMED"),
    (440383, "Depressive disorder", "SNOMED"),
    (4329847, "Myocardial infarction", "SNOMED"),
    (192671, "Gastrointestinal hemorrhage", "SNOMED"),
    (313217, "Atrial fibrillation", "SNOMED"),
    (4112343, "Chronic kidney disease", "SNOMED"),
    (4145356, "Acute renal failure", "SNOMED"),
    (4030840, "Pneumonia", "SNOMED"),
    (192279, "Stroke", "SNOMED"),
    (255848, "Pneumonia, organism unspecified", "SNOMED"),
    (4083487, "Iron deficiency anemia", "SNOMED"),
    (433736, "Obesity", "SNOMED"),
    (4180628, "Heart failure", "SNOMED"),
]
DRUG_CONCEPTS = [
    (1503297, "Metformin", "RxNorm"),
    (1308216, "Lisinopril", "RxNorm"),
    (1539403, "Atorvastatin", "RxNorm"),
    (1518254, "Simvastatin", "RxNorm"),
    (1310149, "Albuterol", "RxNorm"),
    (1112807, "Aspirin", "RxNorm"),
    (1124957, "Ibuprofen", "RxNorm"),
    (1125315, "Acetaminophen", "RxNorm"),
    (40165636, "Sertraline", "RxNorm"),
    (1395058, "Hydrochlorothiazide", "RxNorm"),
    (1110410, "Levothyroxine", "RxNorm"),
    (923672, "Omeprazole", "RxNorm"),
    (19078461, "Amlodipine", "RxNorm"),
]
PROCEDURE_CONCEPTS = [
    (4047862, "Computed tomography", "SNOMED"),
    (4087701, "Magnetic resonance imaging", "SNOMED"),
    (4080812, "Echocardiography", "SNOMED"),
    (4108289, "Electrocardiogram", "SNOMED"),
    (4216219, "Endoscopy", "SNOMED"),
    (4108290, "Coronary angiography", "SNOMED"),
    (4035757, "Hemodialysis", "SNOMED"),
    (40756884, "Total knee replacement", "SNOMED"),
]
MEASUREMENT_CONCEPTS = [
    (3013682, "Hemoglobin", "LOINC", 12.0, 17.0, 8713),  # g/dL
    (3004501, "Glucose", "LOINC", 70.0, 99.0, 8840),  # mg/dL
    (3027597, "HbA1c", "LOINC", 4.0, 6.0, 8554),  # percent
    (3013721, "Cholesterol", "LOINC", 130.0, 200.0, 8840),
    (3022192, "Triglycerides", "LOINC", 50.0, 150.0, 8840),
    (3019550, "Sodium", "LOINC", 135.0, 145.0, 8753),  # mEq/L
    (3023103, "Potassium", "LOINC", 3.5, 5.0, 8753),
    (3016723, "Creatinine", "LOINC", 0.6, 1.2, 8840),
    (3024171, "Heart rate", "LOINC", 60.0, 100.0, 8483),  # /min
    (3004249, "Systolic blood pressure", "LOINC", 100.0, 140.0, 8876),  # mm[Hg]
]
UNITS_LOOKUP = {
    8713: "g/dL", 8840: "mg/dL", 8554: "%", 8753: "mEq/L", 8483: "/min", 8876: "mm[Hg]",
}


def _concept(ctx):
    rows = []
    for cid, name, vocab in CONDITION_CONCEPTS:
        rows.append((cid, name, "Condition", vocab, "Clinical Finding", "S"))
    for cid, name, vocab in DRUG_CONCEPTS:
        rows.append((cid, name, "Drug", vocab, "Ingredient", "S"))
    for cid, name, vocab in PROCEDURE_CONCEPTS:
        rows.append((cid, name, "Procedure", vocab, "Procedure", "S"))
    for cid, name, vocab, _, _, _ in MEASUREMENT_CONCEPTS:
        rows.append((cid, name, "Measurement", vocab, "Lab Test", "S"))
    rows.append((8507, "MALE", "Gender", "Gender", "Gender", "S"))
    rows.append((8532, "FEMALE", "Gender", "Gender", "Gender", "S"))
    rows.append((9201, "Inpatient Visit", "Visit", "Visit", "Visit", "S"))
    rows.append((9202, "Outpatient Visit", "Visit", "Visit", "Visit", "S"))
    rows.append((9203, "Emergency Room Visit", "Visit", "Visit", "Visit", "S"))
    rows.append((9238, "Pharmacy Visit", "Visit", "Visit", "Visit", "S"))
    rows.append((581477, "Office Visit", "Visit", "Visit", "Visit", "S"))
    return pd.DataFrame(rows, columns=[
        "concept_id", "concept_name", "domain_id", "vocabulary_id", "concept_class_id", "standard_concept",
    ])


def _person(ctx, n=15_000):
    rng = ctx.rng
    yob = rng.integers(1925, 2020, size=n)
    return pd.DataFrame({
        "person_id": np.arange(1, n + 1),
        "gender_concept_id": rng.choice([8532, 8507, 0], size=n, p=[0.51, 0.48, 0.01]),
        "year_of_birth": yob,
        "month_of_birth": rng.integers(1, 13, size=n),
        "day_of_birth": rng.integers(1, 29, size=n),
        "race_concept_id": rng.choice([8527, 8516, 8515, 8522, 0], size=n, p=[0.62, 0.13, 0.06, 0.05, 0.14]),
        "ethnicity_concept_id": rng.choice([38003563, 38003564, 0], size=n, p=[0.18, 0.78, 0.04]),
        "location_id": rng.integers(1, 5_000, size=n),
        "provider_id": rng.integers(1, 5_000, size=n),
        "care_site_id": rng.integers(1, 1_500, size=n),
        "person_source_value": [f"PT{i:08d}" for i in range(1, n + 1)],
    })


def _observation_period(ctx, persons):
    rng = ctx.rng
    n = len(persons)
    start = pd.to_datetime(rng.integers(int(pd.Timestamp("2010-01-01").timestamp()), int(pd.Timestamp("2024-01-01").timestamp()), size=n), unit="s")
    duration_d = rng.integers(180, 365 * 10, size=n)
    return pd.DataFrame({
        "observation_period_id": np.arange(1, n + 1),
        "person_id": persons["person_id"].to_numpy(),
        "observation_period_start_date": start.date,
        "observation_period_end_date": (start + pd.to_timedelta(duration_d, unit="D")).date,
        "period_type_concept_id": 44814724,  # Period inferred by algorithm
    })


def _visit_occurrence(ctx, persons, n=120_000):
    rng = ctx.rng
    start = daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30"))
    duration_h = rng.gamma(1.5, 4, size=n).clip(0.25, 24 * 30)
    return pd.DataFrame({
        "visit_occurrence_id": np.arange(1, n + 1),
        "person_id": rng.choice(persons["person_id"].to_numpy(), size=n),
        "visit_concept_id": rng.choice(VISIT_CONCEPTS, size=n, p=[0.10, 0.55, 0.07, 0.08, 0.20]),
        "visit_start_date": start.date,
        "visit_start_datetime": start,
        "visit_end_date": (start + pd.to_timedelta(duration_h, unit="h")).date,
        "visit_end_datetime": start + pd.to_timedelta(duration_h, unit="h"),
        "visit_type_concept_id": 32817,  # EHR
        "provider_id": rng.integers(1, 5_000, size=n),
        "care_site_id": rng.integers(1, 1_500, size=n),
        "visit_source_value": rng.choice(["IP", "OP", "ER", "OF", "TH"], size=n),
        "admitting_source_concept_id": 0,
        "discharge_to_concept_id": 0,
    })


def _condition_occurrence(ctx, persons, visits, n=200_000):
    rng = ctx.rng
    cond = rng.integers(0, len(CONDITION_CONCEPTS), size=n)
    start = daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "condition_occurrence_id": np.arange(1, n + 1),
        "person_id": rng.choice(persons["person_id"].to_numpy(), size=n),
        "condition_concept_id": [CONDITION_CONCEPTS[i][0] for i in cond],
        "condition_start_date": start.date,
        "condition_start_datetime": start,
        "condition_end_date": (start + pd.to_timedelta(rng.integers(1, 720, size=n), unit="D")).date,
        "condition_type_concept_id": rng.choice([32020, 32817, 38000245], size=n),  # EHR encounter / EHR / observation
        "stop_reason": np.where(rng.random(n) < 0.4, rng.choice(["RESOLVED", "INACTIVE", "REMISSION"], size=n), None),
        "provider_id": rng.integers(1, 5_000, size=n),
        "visit_occurrence_id": rng.choice(visits["visit_occurrence_id"].to_numpy(), size=n),
        "condition_source_value": [CONDITION_CONCEPTS[i][1] for i in cond],
        "condition_status_concept_id": rng.choice([4230359, 4084167, 0], size=n),  # Active/Resolved/Other
    })


def _drug_exposure(ctx, persons, visits, n=300_000):
    rng = ctx.rng
    di = rng.integers(0, len(DRUG_CONCEPTS), size=n)
    start = daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30"))
    days_supply = rng.choice([7, 14, 30, 60, 90], size=n)
    return pd.DataFrame({
        "drug_exposure_id": np.arange(1, n + 1),
        "person_id": rng.choice(persons["person_id"].to_numpy(), size=n),
        "drug_concept_id": [DRUG_CONCEPTS[i][0] for i in di],
        "drug_exposure_start_date": start.date,
        "drug_exposure_start_datetime": start,
        "drug_exposure_end_date": (start + pd.to_timedelta(days_supply, unit="D")).date,
        "drug_type_concept_id": rng.choice([38000175, 32817, 32020], size=n),  # Prescription/EHR/Inpatient admin
        "stop_reason": np.where(rng.random(n) < 0.15, rng.choice(["TREATMENT_COMPLETED", "ADVERSE_EVENT", "INEFFECTIVE", "PATIENT_REQUEST"], size=n), None),
        "refills": rng.integers(0, 6, size=n),
        "quantity": rng.choice([14, 30, 60, 90, 180], size=n),
        "days_supply": days_supply,
        "sig": rng.choice(["1 tab po qd", "1 tab po bid", "2 tab po qd", "as needed"], size=n),
        "route_concept_id": 4132161,  # Oral
        "provider_id": rng.integers(1, 5_000, size=n),
        "visit_occurrence_id": rng.choice(visits["visit_occurrence_id"].to_numpy(), size=n),
        "drug_source_value": [DRUG_CONCEPTS[i][1] for i in di],
    })


def _procedure_occurrence(ctx, persons, visits, n=80_000):
    rng = ctx.rng
    pi = rng.integers(0, len(PROCEDURE_CONCEPTS), size=n)
    start = daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "procedure_occurrence_id": np.arange(1, n + 1),
        "person_id": rng.choice(persons["person_id"].to_numpy(), size=n),
        "procedure_concept_id": [PROCEDURE_CONCEPTS[i][0] for i in pi],
        "procedure_date": start.date,
        "procedure_datetime": start,
        "procedure_type_concept_id": rng.choice([38000275, 32817], size=n),
        "modifier_concept_id": 0,
        "quantity": rng.integers(1, 4, size=n),
        "provider_id": rng.integers(1, 5_000, size=n),
        "visit_occurrence_id": rng.choice(visits["visit_occurrence_id"].to_numpy(), size=n),
        "procedure_source_value": [PROCEDURE_CONCEPTS[i][1] for i in pi],
    })


def _measurement(ctx, persons, visits, n=400_000):
    rng = ctx.rng
    mi = rng.integers(0, len(MEASUREMENT_CONCEPTS), size=n)
    rows = [MEASUREMENT_CONCEPTS[i] for i in mi]
    cid = [r[0] for r in rows]
    name = [r[1] for r in rows]
    lows = np.array([r[3] for r in rows])
    highs = np.array([r[4] for r in rows])
    units = np.array([r[5] for r in rows])
    val = lows + (highs - lows) * rng.random(n)
    abn = rng.random(n) < 0.05
    val = np.where(abn, val * rng.uniform(1.4, 2.5, size=n), val)
    start = daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "measurement_id": np.arange(1, n + 1),
        "person_id": rng.choice(persons["person_id"].to_numpy(), size=n),
        "measurement_concept_id": cid,
        "measurement_date": start.date,
        "measurement_datetime": start,
        "measurement_type_concept_id": rng.choice([44818702, 44818701, 32817], size=n),  # Lab result / EHR
        "operator_concept_id": 0,
        "value_as_number": np.round(val, 3),
        "value_as_concept_id": 0,
        "unit_concept_id": units,
        "range_low": lows,
        "range_high": highs,
        "provider_id": rng.integers(1, 5_000, size=n),
        "visit_occurrence_id": rng.choice(visits["visit_occurrence_id"].to_numpy(), size=n),
        "measurement_source_value": name,
    })


def _cohort(ctx, persons, n=20_000):
    rng = ctx.rng
    start = pd.to_datetime(rng.integers(int(pd.Timestamp("2018-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "cohort_definition_id": rng.integers(1, 200, size=n),
        "subject_id": rng.choice(persons["person_id"].to_numpy(), size=n),
        "cohort_start_date": start.date,
        "cohort_end_date": (start + pd.to_timedelta(rng.integers(30, 365 * 5, size=n), unit="D")).date,
    })


def _cohort_attribute(ctx, cohort, n_target=15_000):
    rng = ctx.rng
    n = min(n_target, len(cohort))
    src = cohort.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "cohort_definition_id": src["cohort_definition_id"].to_numpy(),
        "subject_id": src["subject_id"].to_numpy(),
        "cohort_start_date": src["cohort_start_date"].to_numpy(),
        "attribute_definition_id": rng.integers(1, 50, size=n),
        "value_as_number": np.round(rng.uniform(0, 100, size=n), 2),
        "value_as_concept_id": rng.choice([8532, 8507, 4230359, 0], size=n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    concept = _concept(ctx)
    person = _person(ctx)
    obs_period = _observation_period(ctx, person)
    visits = _visit_occurrence(ctx, person)
    conditions = _condition_occurrence(ctx, person, visits)
    drugs = _drug_exposure(ctx, person, visits)
    procedures = _procedure_occurrence(ctx, person, visits)
    measurements = _measurement(ctx, person, visits)
    cohort = _cohort(ctx, person)
    cohort_attr = _cohort_attribute(ctx, cohort)
    tables = {
        "concept": concept,
        "person": person,
        "observation_period": obs_period,
        "visit_occurrence": visits,
        "condition_occurrence": conditions,
        "drug_exposure": drugs,
        "procedure_occurrence": procedures,
        "measurement": measurements,
        "cohort": cohort,
        "cohort_attribute": cohort_attr,
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
