"""
Synthetic EHR Integrations data (HL7 FHIR R4 + USCDI v3).

Entities (>=10): organization, practitioner, patient, encounter, condition,
observation, medication_request, allergy_intolerance, immunization, coverage,
procedure, diagnostic_report.

Realism:
  - Observations carry LOINC code patterns (real LOINC families like 2160-0
    serum creatinine, 718-7 hemoglobin, 8310-5 body temp, 8480-6 systolic BP).
  - Conditions use SNOMED CT and ICD-10-CM dotted codes.
  - Medications use RxNorm RXCUIs.
  - Encounter class codes follow the FHIR HL7 v3 ActCode value set
    (AMB|EMER|IMP|HH|VR).
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

SUBDOMAIN = "ehr_integrations"

# Real LOINC codes commonly seen in EHR observation feeds.
LOINC_OBS = [
    ("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", "mg/dL", 0.6, 1.4, "laboratory"),
    ("718-7", "Hemoglobin [Mass/volume] in Blood", "g/dL", 12.0, 17.0, "laboratory"),
    ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "%", 5.0, 7.5, "laboratory"),
    ("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "mg/dL", 70.0, 140.0, "laboratory"),
    ("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "mg/dL", 130.0, 240.0, "laboratory"),
    ("2571-8", "Triglyceride [Mass/volume] in Serum or Plasma", "mg/dL", 70.0, 250.0, "laboratory"),
    ("777-3", "Platelets [#/volume] in Blood by Automated count", "10*3/uL", 150.0, 400.0, "laboratory"),
    ("6690-2", "Leukocytes [#/volume] in Blood by Automated count", "10*3/uL", 4.0, 11.0, "laboratory"),
    ("8310-5", "Body temperature", "Cel", 36.1, 38.3, "vital-signs"),
    ("8480-6", "Systolic blood pressure", "mm[Hg]", 100.0, 160.0, "vital-signs"),
    ("8462-4", "Diastolic blood pressure", "mm[Hg]", 60.0, 100.0, "vital-signs"),
    ("8867-4", "Heart rate", "/min", 50.0, 110.0, "vital-signs"),
    ("9279-1", "Respiratory rate", "/min", 12.0, 22.0, "vital-signs"),
    ("2710-2", "Oxygen saturation in Blood", "%", 90.0, 100.0, "vital-signs"),
    ("29463-7", "Body weight", "kg", 50.0, 110.0, "vital-signs"),
    ("8302-2", "Body height", "cm", 150.0, 195.0, "vital-signs"),
]

ICD10_CONDITIONS = [
    ("E11.9", "Type 2 diabetes mellitus without complications"),
    ("I10", "Essential (primary) hypertension"),
    ("J45.909", "Unspecified asthma, uncomplicated"),
    ("F32.9", "Major depressive disorder, single episode, unspecified"),
    ("M54.5", "Low back pain"),
    ("J06.9", "Acute upper respiratory infection, unspecified"),
    ("Z00.00", "General adult medical examination without abnormal findings"),
    ("E78.5", "Hyperlipidemia, unspecified"),
    ("K21.9", "Gastro-esophageal reflux disease without esophagitis"),
    ("N39.0", "Urinary tract infection, site not specified"),
    ("R51", "Headache"),
    ("J20.9", "Acute bronchitis, unspecified"),
    ("M25.561", "Pain in right knee"),
    ("R10.9", "Unspecified abdominal pain"),
    ("I48.91", "Unspecified atrial fibrillation"),
]

RXNORM_MEDS = [
    ("197361", "Lisinopril 10 MG Oral Tablet"),
    ("314076", "Lisinopril 5 MG Oral Tablet"),
    ("860975", "Metformin hydrochloride 500 MG Oral Tablet"),
    ("866516", "Metformin hydrochloride 1000 MG Oral Tablet"),
    ("198440", "Atorvastatin 20 MG Oral Tablet"),
    ("617318", "Atorvastatin 40 MG Oral Tablet"),
    ("310965", "Albuterol 0.09 MG/ACTUAT Inhalation Solution"),
    ("313782", "Acetaminophen 500 MG Oral Tablet"),
    ("197517", "Ibuprofen 400 MG Oral Tablet"),
    ("308136", "Amoxicillin 500 MG Oral Capsule"),
    ("204385", "Sertraline 50 MG Oral Tablet"),
    ("197591", "Hydrochlorothiazide 25 MG Oral Tablet"),
    ("314077", "Levothyroxine sodium 0.05 MG Oral Tablet"),
    ("197604", "Omeprazole 20 MG Oral Capsule"),
]


def _organizations(ctx, n=1_000):
    rng = ctx.rng
    f = ctx.faker
    states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "MA", "WA", "GA"]
    return pd.DataFrame({
        "organization_id": [f"ORG{i:06d}" for i in range(1, n + 1)],
        "identifier_npi": [f"{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "type_code": weighted_choice(rng, ["prov", "ins", "lab", "rx", "edu"], [0.55, 0.20, 0.15, 0.05, 0.05], n),
        "name": [f"{f.last_name()} {rng.choice(['Health', 'Medical Center', 'Hospital', 'Clinic', 'Group'])}" for _ in range(n)],
        "telecom_phone": [f.phone_number() for _ in range(n)],
        "address_state": rng.choice(states, size=n),
        "active": rng.random(n) < 0.97,
    })


def _practitioners(ctx, orgs, n=2_500):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "practitioner_id": [f"PRC{i:07d}" for i in range(1, n + 1)],
        "npi": [f"{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "family_name": [f.last_name() for _ in range(n)],
        "given_names": [f.first_name() for _ in range(n)],
        "gender": weighted_choice(rng, ["male", "female", "other"], [0.50, 0.48, 0.02], n),
        "qualification_code": weighted_choice(rng, ["MD", "DO", "NP", "PA", "RN"], [0.60, 0.10, 0.15, 0.10, 0.05], n),
        "qualification_issuer_org_id": rng.choice(orgs["organization_id"].to_numpy(), size=n),
        "active": rng.random(n) < 0.95,
    })


def _patients(ctx, orgs, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "MA", "WA", "GA"]
    return pd.DataFrame({
        "patient_id": [f"PAT{i:08d}" for i in range(1, n + 1)],
        "identifier_mrn": [f"MRN{rng.integers(10**7, 10**8):08d}" for _ in range(n)],
        "family_name": [f.last_name() for _ in range(n)],
        "given_names": [f.first_name() for _ in range(n)],
        "gender": weighted_choice(rng, ["female", "male", "other", "unknown"], [0.50, 0.48, 0.01, 0.01], n),
        "birth_date": pd.to_datetime(rng.integers(int(pd.Timestamp("1925-01-01").timestamp()), int(pd.Timestamp("2024-01-01").timestamp()), size=n), unit="s").date,
        "marital_status_code": weighted_choice(rng, ["S", "M", "D", "W", "U"], [0.35, 0.45, 0.10, 0.05, 0.05], n),
        "race_code": weighted_choice(rng, ["2106-3", "2054-5", "2028-9", "1002-5", "2076-8", "UNK"], [0.55, 0.13, 0.06, 0.01, 0.05, 0.20], n),
        "ethnicity_code": weighted_choice(rng, ["2186-5", "2135-2", "UNK"], [0.65, 0.20, 0.15], n),
        "address_state": rng.choice(states, size=n),
        "address_country": "US",
        "managing_organization_id": rng.choice(orgs["organization_id"].to_numpy(), size=n),
        "language_code": weighted_choice(rng, ["en", "es", "zh", "vi", "fr"], [0.78, 0.13, 0.04, 0.03, 0.02], n),
    })


def _encounters(ctx, patients, practitioners, orgs, n=40_000):
    rng = ctx.rng
    period_start = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    duration_min = rng.gamma(2.5, 18, size=n).clip(5, 1440).astype(int)
    period_end = period_start + pd.to_timedelta(duration_min, unit="m")
    return pd.DataFrame({
        "encounter_id": [f"ENC{i:09d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["finished", "in-progress", "cancelled", "planned"], [0.85, 0.05, 0.05, 0.05], n),
        "class_code": weighted_choice(rng, ["AMB", "EMER", "IMP", "HH", "VR"], [0.70, 0.12, 0.10, 0.05, 0.03], n),
        "type_code": weighted_choice(rng, ["wellness", "follow-up", "urgent-care", "consult", "telehealth"], [0.30, 0.30, 0.15, 0.15, 0.10], n),
        "primary_practitioner_id": rng.choice(practitioners["practitioner_id"].to_numpy(), size=n),
        "service_provider_org_id": rng.choice(orgs["organization_id"].to_numpy(), size=n),
        "period_start": period_start,
        "period_end": period_end,
        "length_minutes": duration_min,
    })


def _observations(ctx, patients, encounters, practitioners, n=200_000):
    rng = ctx.rng
    loinc_idx = rng.integers(0, len(LOINC_OBS), size=n)
    rows = [LOINC_OBS[i] for i in loinc_idx]
    code_value = [r[0] for r in rows]
    code_display = [r[1] for r in rows]
    units = [r[2] for r in rows]
    lows = np.array([r[3] for r in rows])
    highs = np.array([r[4] for r in rows])
    cats = [r[5] for r in rows]
    values = lows + (highs - lows) * rng.random(n)
    # Add ~3% out-of-range "abnormal" results.
    abnormal = rng.random(n) < 0.03
    values = np.where(abnormal, values * rng.uniform(1.4, 2.2, size=n), values)
    interpretation = np.where(abnormal, np.where(rng.random(n) < 0.5, "H", "L"), "N")
    eff = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "observation_id": [f"OBS{i:010d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "encounter_id": rng.choice(encounters["encounter_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["final", "amended", "preliminary"], [0.92, 0.05, 0.03], n),
        "category_code": cats,
        "code_system": "http://loinc.org",
        "code_value": code_value,
        "code_display": code_display,
        "effective_date_time": eff,
        "issued": eff + pd.to_timedelta(rng.integers(1, 720, size=n), unit="m"),
        "value_quantity_value": np.round(values, 2),
        "value_quantity_unit": units,
        "interpretation_code": interpretation,
        "reference_range_low": lows,
        "reference_range_high": highs,
        "performer_id": rng.choice(practitioners["practitioner_id"].to_numpy(), size=n),
    })


def _conditions(ctx, patients, encounters, n=60_000):
    rng = ctx.rng
    idx = rng.integers(0, len(ICD10_CONDITIONS), size=n)
    code = [ICD10_CONDITIONS[i][0] for i in idx]
    disp = [ICD10_CONDITIONS[i][1] for i in idx]
    return pd.DataFrame({
        "condition_id": [f"CND{i:09d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "encounter_id": rng.choice(encounters["encounter_id"].to_numpy(), size=n),
        "clinical_status_code": weighted_choice(rng, ["active", "resolved", "remission", "inactive"], [0.50, 0.30, 0.10, 0.10], n),
        "verification_status_code": weighted_choice(rng, ["confirmed", "provisional", "differential"], [0.80, 0.15, 0.05], n),
        "category_code": weighted_choice(rng, ["problem-list-item", "encounter-diagnosis", "health-concern"], [0.50, 0.40, 0.10], n),
        "severity_code": weighted_choice(rng, ["mild", "moderate", "severe"], [0.55, 0.35, 0.10], n),
        "code_system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code_value": code,
        "code_display": disp,
        "onset_date_time": daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30")),
        "recorded_date": daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30")).date,
    })


def _medication_requests(ctx, patients, encounters, practitioners, n=80_000):
    rng = ctx.rng
    idx = rng.integers(0, len(RXNORM_MEDS), size=n)
    code = [RXNORM_MEDS[i][0] for i in idx]
    disp = [RXNORM_MEDS[i][1] for i in idx]
    authored = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "medication_request_id": [f"MRQ{i:09d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "encounter_id": rng.choice(encounters["encounter_id"].to_numpy(), size=n),
        "requester_id": rng.choice(practitioners["practitioner_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["active", "completed", "cancelled", "stopped", "draft"], [0.45, 0.40, 0.05, 0.05, 0.05], n),
        "intent": weighted_choice(rng, ["order", "plan", "proposal"], [0.85, 0.10, 0.05], n),
        "priority": weighted_choice(rng, ["routine", "urgent", "stat"], [0.85, 0.12, 0.03], n),
        "medication_code_system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "medication_code_value": code,
        "medication_display": disp,
        "dose_quantity_value": np.round(rng.choice([1.0, 2.0, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0, 500.0, 1000.0], size=n), 1),
        "dose_quantity_unit": rng.choice(["mg", "mL", "tab", "unit", "puff"], size=n),
        "route_code": weighted_choice(rng, ["PO", "IV", "IM", "SC", "INH"], [0.70, 0.12, 0.08, 0.05, 0.05], n),
        "frequency_text": weighted_choice(rng, ["once daily", "twice daily", "three times daily", "every 4 hours", "as needed"], [0.40, 0.30, 0.15, 0.10, 0.05], n),
        "authored_on": authored,
        "dispense_quantity": np.round(rng.choice([30.0, 60.0, 90.0, 14.0, 7.0], size=n), 1),
        "dispense_refills_allowed": rng.integers(0, 6, size=n),
        "substitution_allowed": rng.random(n) < 0.85,
    })


def _allergy_intolerance(ctx, patients, n=12_000):
    rng = ctx.rng
    substances = [
        ("7980", "Penicillin G"), ("1191", "Aspirin"), ("5640", "Ibuprofen"),
        ("733", "Amoxicillin"), ("FOOD-PEANUT", "Peanut"), ("FOOD-SHELLFISH", "Shellfish"),
        ("FOOD-EGG", "Egg"), ("ENV-LATEX", "Latex"), ("ENV-DUST", "House dust mite"),
    ]
    idx = rng.integers(0, len(substances), size=n)
    return pd.DataFrame({
        "allergy_id": [f"ALG{i:08d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "clinical_status_code": weighted_choice(rng, ["active", "resolved", "inactive"], [0.85, 0.10, 0.05], n),
        "verification_status_code": weighted_choice(rng, ["confirmed", "unconfirmed"], [0.80, 0.20], n),
        "type": weighted_choice(rng, ["allergy", "intolerance"], [0.75, 0.25], n),
        "category": weighted_choice(rng, ["medication", "food", "environment", "biologic"], [0.45, 0.30, 0.20, 0.05], n),
        "criticality": weighted_choice(rng, ["low", "high", "unable-to-assess"], [0.55, 0.35, 0.10], n),
        "substance_code_value": [substances[i][0] for i in idx],
        "substance_display": [substances[i][1] for i in idx],
        "reaction_severity": weighted_choice(rng, ["mild", "moderate", "severe"], [0.55, 0.35, 0.10], n),
        "onset_date_time": daterange_minutes(rng, n, pd.Timestamp("2010-01-01"), pd.Timestamp("2026-01-01")),
    })


def _immunizations(ctx, patients, encounters, practitioners, n=50_000):
    rng = ctx.rng
    cvx = [
        ("207", "COVID-19, mRNA, LNP-S, PF, 100 mcg/0.5 mL dose"),
        ("141", "Influenza, seasonal, injectable"),
        ("133", "Pneumococcal conjugate PCV 13"),
        ("115", "Tdap"),
        ("121", "Zoster, live"),
        ("83", "Hepatitis A, ped/adol, 2 dose"),
        ("08", "Hepatitis B, adolescent or pediatric, 3 dose"),
        ("03", "MMR"),
    ]
    idx = rng.integers(0, len(cvx), size=n)
    return pd.DataFrame({
        "immunization_id": [f"IMM{i:09d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "encounter_id": rng.choice(encounters["encounter_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["completed", "entered-in-error", "not-done"], [0.96, 0.02, 0.02], n),
        "vaccine_code_system": "http://hl7.org/fhir/sid/cvx",
        "vaccine_code_value": [cvx[i][0] for i in idx],
        "occurrence_date_time": daterange_minutes(rng, n, pd.Timestamp("2018-01-01"), pd.Timestamp("2026-04-30")),
        "lot_number": [f"LOT{rng.integers(10000, 99999)}" for _ in range(n)],
        "site_code": weighted_choice(rng, ["LA", "RA", "LD", "RD"], [0.40, 0.40, 0.10, 0.10], n),
        "route_code": weighted_choice(rng, ["IM", "SC", "IN", "PO"], [0.85, 0.10, 0.04, 0.01], n),
        "dose_quantity": np.round(rng.choice([0.25, 0.5, 1.0], size=n), 2),
        "dose_quantity_unit": "mL",
        "performer_id": rng.choice(practitioners["practitioner_id"].to_numpy(), size=n),
    })


def _coverage(ctx, patients, orgs, n=12_000):
    rng = ctx.rng
    payor_pool = orgs[orgs["type_code"] == "ins"]["organization_id"].to_numpy()
    if len(payor_pool) == 0:
        payor_pool = orgs["organization_id"].to_numpy()
    return pd.DataFrame({
        "coverage_id": [f"COV{i:08d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["active", "cancelled", "draft"], [0.90, 0.07, 0.03], n),
        "type_code": weighted_choice(rng, ["EHCPOL", "DENTAL", "MEDICARE", "MEDICAID", "PPO"], [0.55, 0.10, 0.15, 0.10, 0.10], n),
        "subscriber_id": [f"SUB{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "payor_org_id": rng.choice(payor_pool, size=n),
        "relationship_code": weighted_choice(rng, ["self", "spouse", "child", "other"], [0.65, 0.18, 0.15, 0.02], n),
        "period_start": pd.to_datetime(rng.integers(int(pd.Timestamp("2018-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s").date,
        "plan_name": rng.choice(["Bronze", "Silver", "Gold", "Platinum", "Basic", "Premium"], size=n),
        "network": weighted_choice(rng, ["in-network", "out-of-network", "open-access"], [0.75, 0.15, 0.10], n),
    })


def _procedures(ctx, patients, encounters, practitioners, n=30_000):
    rng = ctx.rng
    cpt = [
        ("99213", "Office/outpatient visit established patient"),
        ("99214", "Office/outpatient visit established patient mod-high"),
        ("36415", "Routine venipuncture"),
        ("80053", "Comprehensive metabolic panel"),
        ("85025", "CBC with automated differential"),
        ("93000", "Electrocardiogram, routine"),
        ("71046", "Chest X-ray, 2 views"),
        ("12001", "Simple repair of superficial wounds"),
        ("90471", "Immunization administration"),
    ]
    idx = rng.integers(0, len(cpt), size=n)
    started = daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "procedure_id": [f"PRO{i:09d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "encounter_id": rng.choice(encounters["encounter_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["completed", "in-progress", "stopped"], [0.92, 0.04, 0.04], n),
        "code_system": "http://www.ama-assn.org/go/cpt",
        "code_value": [cpt[i][0] for i in idx],
        "code_display": [cpt[i][1] for i in idx],
        "performed_period_start": started,
        "performed_period_end": started + pd.to_timedelta(rng.integers(5, 240, size=n), unit="m"),
        "performer_id": rng.choice(practitioners["practitioner_id"].to_numpy(), size=n),
        "outcome_code": weighted_choice(rng, ["successful", "unsuccessful", "partial"], [0.92, 0.04, 0.04], n),
    })


def _diagnostic_reports(ctx, patients, encounters, practitioners, orgs, n=20_000):
    rng = ctx.rng
    return pd.DataFrame({
        "diagnostic_report_id": [f"DXR{i:08d}" for i in range(1, n + 1)],
        "patient_id": rng.choice(patients["patient_id"].to_numpy(), size=n),
        "encounter_id": rng.choice(encounters["encounter_id"].to_numpy(), size=n),
        "status": weighted_choice(rng, ["final", "amended", "preliminary", "cancelled"], [0.85, 0.05, 0.07, 0.03], n),
        "category_code": weighted_choice(rng, ["LAB", "RAD", "PAT", "CARD"], [0.55, 0.25, 0.10, 0.10], n),
        "code_system": "http://loinc.org",
        "code_value": rng.choice(["57021-8", "11502-2", "24323-8", "30954-2"], size=n),
        "effective_date_time": daterange_minutes(rng, n, pd.Timestamp("2022-01-01"), pd.Timestamp("2026-04-30")),
        "performer_org_id": rng.choice(orgs["organization_id"].to_numpy(), size=n),
        "results_interpreter_id": rng.choice(practitioners["practitioner_id"].to_numpy(), size=n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    organizations = _organizations(ctx)
    practitioners = _practitioners(ctx, organizations)
    patients = _patients(ctx, organizations)
    encounters = _encounters(ctx, patients, practitioners, organizations)
    observations = _observations(ctx, patients, encounters, practitioners)
    conditions = _conditions(ctx, patients, encounters)
    medication_requests = _medication_requests(ctx, patients, encounters, practitioners)
    allergies = _allergy_intolerance(ctx, patients)
    immunizations = _immunizations(ctx, patients, encounters, practitioners)
    coverage = _coverage(ctx, patients, organizations)
    procedures = _procedures(ctx, patients, encounters, practitioners)
    diagnostic_reports = _diagnostic_reports(ctx, patients, encounters, practitioners, organizations)
    tables = {
        "organization": organizations,
        "practitioner": practitioners,
        "patient": patients,
        "encounter": encounters,
        "observation": observations,
        "condition": conditions,
        "medication_request": medication_requests,
        "allergy_intolerance": allergies,
        "immunization": immunizations,
        "coverage": coverage,
        "procedure": procedures,
        "diagnostic_report": diagnostic_reports,
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
