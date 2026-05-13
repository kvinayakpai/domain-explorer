"""
Synthetic Loss Prevention data — POS exceptions, incidents, ORC investigations,
return abuse, refund-fraud scoring, and store-level shrink snapshots.

Vendor anchors:
  NCR Voyix LP, Oracle XStore LP (XBR), Sensormatic ShrinkVision (JCI),
  Auror ORC, Appriss Retail Verify, Profitect (Zebra), Aptos LP,
  Tyco RFID / Detego, Indyme, ALTO Alliance, Zebra Reflexis,
  Honeywell Connected Retail, RetailNext, Datalogic, NCR Counterpoint.

Scale targets (single year, single chain):
  ~200 stores × ~500k transactions/day chain-wide × 365 days
  = pos_transaction sampled to ~500k synthetic rows (representative grain)
  ~365k pos_exceptions (~0.5% of full chain volume across the year, sampled to 365k)
  ~50k incidents, ~10k investigations, ~5k recoveries, ~24k shrink snapshots.

All large IDs use the int64-safe pattern (numpy rng.integers + zero-padded
format string) consistent with the capital_markets/agentic_commerce generators.
PII columns are pre-hashed at generation time — never store raw names/plates.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table  # noqa: E402

SUBDOMAIN = "loss_prevention"
TENANT_SALT = "lp-tenant-salt-2026"

REGIONS = ["West", "Midwest", "Northeast", "Southeast", "Southwest", "Mountain"]
FORMATS = ["hypermarket", "supermarket", "specialty", "convenience", "ecom_dc"]
FORMAT_W = [0.10, 0.55, 0.22, 0.10, 0.03]
STAFFING_TIERS = ["T1", "T2", "T3"]
STAFFING_W = [0.20, 0.50, 0.30]

EMPLOYEE_ROLES = ["cashier", "supervisor", "asset_protection", "manager", "stocker"]
EMPLOYEE_ROLE_W = [0.55, 0.15, 0.06, 0.10, 0.14]
EMPLOYEE_STATUS = ["active", "terminated", "investigation", "on_leave"]
EMPLOYEE_STATUS_W = [0.90, 0.06, 0.01, 0.03]

DEPARTMENTS = [
    "apparel", "footwear", "electronics", "beauty", "fragrance",
    "consumables", "spirits", "tobacco", "home", "toys",
    "OTC_pharmacy", "small_appliance", "tools", "auto", "sporting_goods",
]

EXCEPTION_TYPES = [
    "sweethearting", "refund_no_receipt", "void_after_tender", "no_sale",
    "cash_skim", "price_override", "barcode_swap", "discount_abuse",
]
EXCEPTION_TYPE_W = [0.18, 0.22, 0.12, 0.08, 0.06, 0.14, 0.10, 0.10]
EXCEPTION_STATUS = ["open", "under_review", "investigation", "closed_unfounded", "closed_confirmed"]
EXCEPTION_STATUS_W = [0.18, 0.20, 0.10, 0.42, 0.10]
EXCEPTION_SOURCES = [
    "NCR_Voyix_LP", "Oracle_XBR", "Profitect", "Aptos_LP",
    "Sensormatic", "Datalogic", "NCR_Counterpoint", "Honeywell",
]
EXCEPTION_SOURCE_W = [0.30, 0.20, 0.14, 0.10, 0.10, 0.07, 0.05, 0.04]

INCIDENT_TYPES = [
    "external_shoplift", "internal_theft", "orc_boost", "burglary",
    "robbery", "return_abuse", "refund_fraud", "cargo_theft",
]
INCIDENT_TYPE_W = [0.46, 0.10, 0.16, 0.04, 0.02, 0.10, 0.10, 0.02]
INCIDENT_STATUS = [
    "open", "investigating", "closed_recovered", "closed_prosecuted",
    "closed_writeoff", "closed_unfounded",
]
INCIDENT_STATUS_W = [0.08, 0.18, 0.28, 0.16, 0.20, 0.10]
DETECTED_VIA = ["exception_alert", "cctv_review", "tip", "customer_report", "audit", "inventory_count"]
DETECTED_VIA_W = [0.42, 0.30, 0.06, 0.06, 0.08, 0.08]
NIBRS_CODES = ["23C", "23D", "23F", "23H", "23G", "26A", "26B", "26E", "120", "210"]

INV_TYPES = ["internal", "external", "orc", "refund_fraud", "sweethearting_audit", "cargo"]
INV_TYPE_W = [0.18, 0.42, 0.14, 0.12, 0.10, 0.04]
INV_STATUS = ["open", "in_progress", "closed_recovered", "closed_prosecuted", "closed_writeoff", "closed_unfounded"]
INV_STATUS_W = [0.10, 0.18, 0.28, 0.14, 0.20, 0.10]

RECOVERY_TYPES = ["cash", "merchandise", "civil_demand", "restitution", "insurance_payout"]
RECOVERY_TYPE_W = [0.18, 0.42, 0.20, 0.14, 0.06]

TENDERS = ["cash", "credit", "debit", "gift", "ebt", "other"]
TENDER_W = [0.20, 0.45, 0.28, 0.04, 0.02, 0.01]

SCORE_SOURCES = ["Appriss_Retail", "internal_xgb", "Auror_offender_signal"]
SCORE_SOURCE_W = [0.66, 0.26, 0.08]
SCORE_RECS = ["approve", "verify", "deny"]
SCORE_REC_W = [0.78, 0.16, 0.06]


def _hash(parts) -> str:
    raw = TENANT_SALT + "|" + "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
def _stores(ctx, n=200):
    rng = ctx.rng
    return pd.DataFrame({
        "store_id":         [f"STR{i:05d}" for i in range(1, n + 1)],
        "store_name":       [f"Store {i:04d}" for i in range(1, n + 1)],
        "banner":           weighted_choice(rng, ["Banner A", "Banner B", "Banner C"], [0.55, 0.30, 0.15], n),
        "region":           rng.choice(REGIONS, size=n),
        "country_iso2":     rng.choice(["US", "CA", "GB", "DE", "FR"], p=[0.78, 0.10, 0.06, 0.04, 0.02], size=n),
        "format":           weighted_choice(rng, FORMATS, FORMAT_W, n),
        "lp_staffing_tier": weighted_choice(rng, STAFFING_TIERS, STAFFING_W, n),
        "eas_enabled":      rng.random(n) < 0.74,
        "rfid_enabled":     rng.random(n) < 0.35,
        "status":           weighted_choice(rng, ["active", "closing", "closed"], [0.95, 0.03, 0.02], n),
    })


def _employees(ctx, stores, n=20_000):
    rng = ctx.rng
    s_idx = rng.integers(0, len(stores), size=n)
    hire = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2018-01-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s")
    status = weighted_choice(rng, EMPLOYEE_STATUS, EMPLOYEE_STATUS_W, n)
    term = np.where(status == "terminated",
                    hire + pd.to_timedelta(rng.integers(60, 2_000, size=n), unit="D"),
                    np.datetime64("NaT"))
    emp_ids = [f"EMP{i:07d}" for i in range(1, n + 1)]
    return pd.DataFrame({
        "employee_id":       emp_ids,
        "employee_ref_hash": [_hash(["HRID", eid]) for eid in emp_ids],
        "home_store_id":     stores["store_id"].to_numpy()[s_idx],
        "role":              weighted_choice(rng, EMPLOYEE_ROLES, EMPLOYEE_ROLE_W, n),
        "hire_date":         hire.date,
        "termination_date":  pd.Series(term).dt.date,
        "status":            status,
    })


def _items(ctx, n=50_000):
    rng = ctx.rng
    cost = (rng.lognormal(4.5, 1.0, size=n) * 100).astype(np.int64)
    retail = (cost * rng.uniform(1.2, 3.5, size=n)).astype(np.int64)
    craved = np.round(rng.beta(2.0, 5.0, size=n) * 10, 2)
    return pd.DataFrame({
        "item_id":           [f"ITM{i:07d}" for i in range(1, n + 1)],
        "gtin":              [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "department":        rng.choice(DEPARTMENTS, size=n),
        "category":          [f"cat-{rng.integers(1, 200):03d}" for _ in range(n)],
        "unit_cost_minor":   cost,
        "unit_retail_minor": retail,
        "craved_score":      craved,
        "eas_protected":     (craved > 6.0) & (rng.random(n) < 0.85),
        "rfid_tagged":       (craved > 5.0) & (rng.random(n) < 0.45),
    })


def _pos_transactions(ctx, stores, employees, n=500_000):
    """Representative sample of POS receipts (full chain would be ~365 * 500k)."""
    rng = ctx.rng
    s_idx = rng.integers(0, len(stores), size=n)
    e_idx = rng.integers(0, len(employees), size=n)
    txn_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-05-12").timestamp()),
                     int(pd.Timestamp("2026-05-11").timestamp()), size=n),
        unit="s")
    gross = (rng.lognormal(3.6, 0.9, size=n) * 100).astype(np.int64)
    discount = (gross * rng.uniform(0.0, 0.30, size=n)).astype(np.int64)
    refund = np.where(rng.random(n) < 0.08,
                      (rng.lognormal(3.5, 0.8, size=n) * 100).astype(np.int64),
                      0).astype(np.int64)
    net = (gross - discount - refund).clip(min=0)
    item_count = rng.integers(1, 25, size=n)
    void_flag = rng.random(n) < 0.015
    no_sale_flag = rng.random(n) < 0.008
    txn_ids = [f"TXN{i:010d}" for i in range(1, n + 1)]
    return pd.DataFrame({
        "transaction_id":         txn_ids,
        "store_id":               stores["store_id"].to_numpy()[s_idx],
        "register_id":            [f"REG{rng.integers(1, 20):02d}" for _ in range(n)],
        "employee_id":            employees["employee_id"].to_numpy()[e_idx],
        "customer_ref_hash":      [_hash(["LYL", rng.integers(1, 10**8)]) if rng.random() < 0.40 else None
                                    for _ in range(n)],
        "txn_ts":                 txn_ts,
        "tender_type":            weighted_choice(rng, TENDERS, TENDER_W, n),
        "gross_amount_minor":     gross,
        "discount_amount_minor":  discount,
        "refund_amount_minor":    refund,
        "net_amount_minor":       net,
        "item_count":             item_count.astype("int32"),
        "void_flag":              void_flag,
        "no_sale_flag":           no_sale_flag,
    })


def _exceptions(ctx, txns, employees, n=365_000):
    """~0.5% exception rate vs full-volume; sampled to 365k for a workable dataset."""
    rng = ctx.rng
    if n > len(txns):
        n = len(txns)
    sub = txns.sample(n=n, random_state=ctx.seed + 1).reset_index(drop=True)
    detected = sub["txn_ts"].to_numpy() + pd.to_timedelta(rng.integers(0, 86400, size=n), unit="s")
    return pd.DataFrame({
        "exception_id":         [f"EXC{i:010d}" for i in range(1, n + 1)],
        "transaction_id":       sub["transaction_id"].to_numpy(),
        "store_id":             sub["store_id"].to_numpy(),
        "employee_id":          sub["employee_id"].to_numpy(),
        "exception_type":       weighted_choice(rng, EXCEPTION_TYPES, EXCEPTION_TYPE_W, n),
        "exception_score":      np.round(rng.beta(2.0, 2.5, size=n), 3),
        "source_system":        weighted_choice(rng, EXCEPTION_SOURCES, EXCEPTION_SOURCE_W, n),
        "detected_at":          detected,
        "status":               weighted_choice(rng, EXCEPTION_STATUS, EXCEPTION_STATUS_W, n),
        "amount_at_risk_minor": (sub["gross_amount_minor"].to_numpy() * rng.uniform(0.05, 1.10, size=n)).astype(np.int64),
        "video_segment_ref":    [f"s3://cctv-cold/{rng.integers(10**10, 10**11):011d}.mp4"
                                 if rng.random() < 0.42 else None for _ in range(n)],
    })


def _suspects(ctx, n=30_000):
    rng = ctx.rng
    first_seen = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                     int(pd.Timestamp("2026-05-01").timestamp()), size=n),
        unit="s")
    last_seen = first_seen + pd.to_timedelta(rng.integers(0, 365, size=n), unit="D")
    orc_flag = rng.random(n) < 0.18
    suspect_ids = [f"SUS{i:08d}" for i in range(1, n + 1)]
    return pd.DataFrame({
        "suspect_id":             suspect_ids,
        "suspect_ref_hash":       [_hash(["SUSPECT", sid]) for sid in suspect_ids],
        "alias_count":            rng.integers(1, 6, size=n).astype("int16"),
        "first_seen_at":          first_seen,
        "last_seen_at":           last_seen,
        "orc_flag":               orc_flag,
        "orc_ring_id":            np.where(orc_flag,
                                            [f"RING{rng.integers(1, 250):04d}" for _ in range(n)],
                                            None),
        "known_vehicle_ref_hash": [_hash(["VEH", rng.integers(1, 10**8)]) if rng.random() < 0.46 else None
                                    for _ in range(n)],
        "auror_offender_id":      [f"AUROR-{rng.integers(10**8, 10**9):09d}" if rng.random() < 0.32 else None
                                    for _ in range(n)],
        "alto_packet_id":         [f"ALTO-{rng.integers(10**6, 10**7):07d}" if rng.random() < 0.18 else None
                                    for _ in range(n)],
    })


def _incidents(ctx, stores, suspects, employees, n=50_000):
    rng = ctx.rng
    s_idx = rng.integers(0, len(stores), size=n)
    sp_idx = rng.integers(0, len(suspects), size=n)
    e_idx = rng.integers(0, len(employees), size=n)
    incident_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-05-12").timestamp()),
                     int(pd.Timestamp("2026-05-11").timestamp()), size=n),
        unit="s")
    gross = (rng.lognormal(5.0, 1.1, size=n) * 100).astype(np.int64)
    recovered = (gross * rng.beta(1.5, 3.5, size=n)).astype(np.int64)
    net = (gross - recovered).clip(min=0)
    return pd.DataFrame({
        "incident_id":             [f"INC{i:08d}" for i in range(1, n + 1)],
        "store_id":                stores["store_id"].to_numpy()[s_idx],
        "incident_type":           weighted_choice(rng, INCIDENT_TYPES, INCIDENT_TYPE_W, n),
        "incident_ts":             incident_ts,
        "reported_by_employee_id": employees["employee_id"].to_numpy()[e_idx],
        "detected_via":            weighted_choice(rng, DETECTED_VIA, DETECTED_VIA_W, n),
        "suspect_id":              suspects["suspect_id"].to_numpy()[sp_idx],
        "gross_loss_minor":        gross,
        "recovered_minor":         recovered,
        "net_loss_minor":          net,
        "nibrs_code":              np.where(rng.random(n) < 0.34,
                                             rng.choice(NIBRS_CODES, size=n),
                                             None),
        "status":                  weighted_choice(rng, INCIDENT_STATUS, INCIDENT_STATUS_W, n),
    })


def _investigations(ctx, incidents, employees, n=10_000):
    rng = ctx.rng
    if n > len(incidents):
        n = len(incidents)
    sub = incidents.sample(n=n, random_state=ctx.seed + 2).reset_index(drop=True)
    e_idx = rng.integers(0, len(employees), size=n)
    opened = sub["incident_ts"].to_numpy() + pd.to_timedelta(rng.integers(0, 7 * 86400, size=n), unit="s")
    closed = opened + pd.to_timedelta(rng.integers(86400, 90 * 86400, size=n), unit="s")
    return pd.DataFrame({
        "investigation_id":       [f"INV{i:08d}" for i in range(1, n + 1)],
        "incident_id":            sub["incident_id"].to_numpy(),
        "opened_by_employee_id":  employees["employee_id"].to_numpy()[e_idx],
        "opened_at":              opened,
        "closed_at":              closed,
        "investigation_type":     weighted_choice(rng, INV_TYPES, INV_TYPE_W, n),
        "status":                 weighted_choice(rng, INV_STATUS, INV_STATUS_W, n),
        "evidence_count":         rng.integers(1, 25, size=n).astype("int32"),
        "video_evidence_minutes": rng.integers(0, 240, size=n).astype("int32"),
        "prosecution_referred":   rng.random(n) < 0.22,
        "alto_shared":            rng.random(n) < 0.12,
        "case_packet_uri":        [f"s3://lp-case-mgmt/cases/{rng.integers(10**10, 10**11):011d}.zip"
                                    for _ in range(n)],
    })


def _recoveries(ctx, incidents, investigations, employees, n=5_000):
    rng = ctx.rng
    recoverable = incidents[incidents["recovered_minor"] > 0].reset_index(drop=True)
    if n > len(recoverable):
        n = len(recoverable)
    sub = recoverable.sample(n=n, random_state=ctx.seed + 3).reset_index(drop=True)
    inv_idx = rng.integers(0, len(investigations), size=n)
    e_idx = rng.integers(0, len(employees), size=n)
    recovered_at = sub["incident_ts"].to_numpy() + pd.to_timedelta(rng.integers(86400, 60 * 86400, size=n), unit="s")
    return pd.DataFrame({
        "recovery_id":              [f"REC{i:08d}" for i in range(1, n + 1)],
        "incident_id":              sub["incident_id"].to_numpy(),
        "investigation_id":         investigations["investigation_id"].to_numpy()[inv_idx],
        "recovered_amount_minor":   (sub["recovered_minor"].to_numpy() * rng.uniform(0.4, 1.0, size=n)).astype(np.int64),
        "recovery_type":            weighted_choice(rng, RECOVERY_TYPES, RECOVERY_TYPE_W, n),
        "recovered_at":             recovered_at,
        "recovered_by_employee_id": employees["employee_id"].to_numpy()[e_idx],
    })


def _fraud_scores(ctx, txns, n=80_000):
    rng = ctx.rng
    if n > len(txns):
        n = len(txns)
    sub = txns.sample(n=n, random_state=ctx.seed + 4).reset_index(drop=True)
    score = np.round(rng.beta(1.6, 4.0, size=n), 3)
    rec = np.where(score >= 0.75, "deny", np.where(score >= 0.45, "verify", "approve"))
    return pd.DataFrame({
        "fraud_score_id":    [f"FSC{i:09d}" for i in range(1, n + 1)],
        "customer_ref_hash": np.where(sub["customer_ref_hash"].notna(),
                                       sub["customer_ref_hash"].fillna(""),
                                       [_hash(["LYL_GUEST", rng.integers(1, 10**8)]) for _ in range(n)]),
        "transaction_id":    sub["transaction_id"].to_numpy(),
        "score_source":      weighted_choice(rng, SCORE_SOURCES, SCORE_SOURCE_W, n),
        "score":             score,
        "recommendation":    rec,
        "scored_at":         sub["txn_ts"].to_numpy() + pd.to_timedelta(rng.integers(0, 600, size=n), unit="s"),
    })


def _shrink_snapshots(ctx, stores, n=24_000):
    """Monthly shrink snapshot per store × department (200 stores × 12 mo × ~10 depts ≈ 24k)."""
    rng = ctx.rng
    rows = []
    months_back = 12
    base_month = pd.Timestamp("2025-05-01")
    snap_idx = 1
    dept_sample = list(DEPARTMENTS[:10])  # cap at 10 dominant departments
    for s_id in stores["store_id"].to_numpy():
        for m in range(months_back):
            period_start = base_month + pd.DateOffset(months=m)
            period_end = (period_start + pd.DateOffset(months=1) - pd.Timedelta(days=1)).date()
            for dept in dept_sample:
                opening = int(rng.lognormal(11.0, 0.7) * 100)
                receipts = int(opening * rng.uniform(0.20, 0.50))
                cogs = int(opening * rng.uniform(0.20, 0.45))
                closing = max(0, opening + receipts - cogs)
                known = int(cogs * rng.uniform(0.002, 0.012))
                unknown = int(cogs * rng.uniform(0.005, 0.025))
                total = known + unknown
                rows.append({
                    "snapshot_id": f"SHK{snap_idx:08d}",
                    "store_id": s_id,
                    "department": dept,
                    "period_start": period_start.date(),
                    "period_end": period_end,
                    "opening_inventory_minor": opening,
                    "receipts_minor": receipts,
                    "cogs_minor": cogs,
                    "closing_inventory_minor": closing,
                    "known_shrink_minor": known,
                    "unknown_shrink_minor": unknown,
                    "total_shrink_minor": total,
                    "shrink_pct": round(total / max(1, cogs), 4),
                })
                snap_idx += 1
                if snap_idx > n:
                    return pd.DataFrame(rows)
    return pd.DataFrame(rows)


def generate(seed=42):
    ctx = make_context(seed)
    print("  generating stores...")
    stores = _stores(ctx)
    print("  generating employees...")
    employees = _employees(ctx, stores)
    print("  generating items...")
    items = _items(ctx)
    print("  generating pos transactions...")
    txns = _pos_transactions(ctx, stores, employees)
    print("  generating pos exceptions (365k)...")
    exceptions = _exceptions(ctx, txns, employees)
    print("  generating suspects...")
    suspects = _suspects(ctx)
    print("  generating incidents...")
    incidents = _incidents(ctx, stores, suspects, employees)
    print("  generating investigations...")
    investigations = _investigations(ctx, incidents, employees)
    print("  generating recoveries...")
    recoveries = _recoveries(ctx, incidents, investigations, employees)
    print("  generating fraud_scores...")
    fraud_scores = _fraud_scores(ctx, txns)
    print("  generating shrink snapshots...")
    shrink = _shrink_snapshots(ctx, stores)

    tables = {
        "store":           stores,
        "employee":        employees,
        "item":            items,
        "pos_transaction": txns,
        "pos_exception":   exceptions,
        "suspect":         suspects,
        "incident":        incidents,
        "investigation":   investigations,
        "recovery":        recoveries,
        "fraud_score":     fraud_scores,
        "shrink_snapshot": shrink,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    tables = generate(args.seed)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
