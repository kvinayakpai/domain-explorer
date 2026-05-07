"""
Synthetic Cloud FinOps data — FOCUS 1.0 (FinOps Open Cost & Usage Spec).

Entities (>=8): billing_account, provider, service, region, invoice,
charge_record, resource_tag, commitment, allocation, budget.

Realism:
  - Charge records use the FOCUS columns (BilledCost, EffectiveCost,
    CommitmentDiscountId, ServiceCategory, etc.)
  - Provider mix mirrors public market share (AWS 32% / Azure 23% / GCP 11%
    of cloud spend, plus the long-tail).
  - Cost shape is lognormal with a small fraction of bursty top-spend resources.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "cloud_finops"

PROVIDERS = ["AWS", "Azure", "GCP", "Oracle", "Alibaba", "IBM"]
PROV_W = [0.45, 0.30, 0.16, 0.04, 0.03, 0.02]

SERVICES = [
    ("EC2", "AWS", "Compute", "Virtual Machines"),
    ("Lambda", "AWS", "Compute", "Serverless"),
    ("EKS", "AWS", "Compute", "Container"),
    ("Fargate", "AWS", "Compute", "Container"),
    ("S3", "AWS", "Storage", "Object Storage"),
    ("EBS", "AWS", "Storage", "Block Storage"),
    ("RDS", "AWS", "Database", "Relational Database"),
    ("DynamoDB", "AWS", "Database", "NoSQL Database"),
    ("CloudFront", "AWS", "Networking", "CDN"),
    ("VPC", "AWS", "Networking", "Virtual Network"),
    ("VirtualMachines", "Azure", "Compute", "Virtual Machines"),
    ("AKS", "Azure", "Compute", "Container"),
    ("Functions", "Azure", "Compute", "Serverless"),
    ("BlobStorage", "Azure", "Storage", "Object Storage"),
    ("SQLDatabase", "Azure", "Database", "Relational Database"),
    ("CosmosDB", "Azure", "Database", "NoSQL Database"),
    ("ComputeEngine", "GCP", "Compute", "Virtual Machines"),
    ("GKE", "GCP", "Compute", "Container"),
    ("CloudRun", "GCP", "Compute", "Serverless"),
    ("CloudStorage", "GCP", "Storage", "Object Storage"),
    ("BigQuery", "GCP", "Analytics", "Data Warehouse"),
    ("PubSub", "GCP", "Networking", "Messaging"),
]

REGIONS = {
    "AWS": ["us-east-1", "us-east-2", "us-west-2", "eu-west-1", "eu-central-1", "ap-south-1", "ap-southeast-1", "ap-northeast-1"],
    "Azure": ["eastus", "westus2", "northeurope", "westeurope", "japaneast", "australiaeast"],
    "GCP": ["us-central1", "us-east1", "europe-west1", "europe-west4", "asia-northeast1", "asia-southeast1"],
    "Oracle": ["us-ashburn-1", "uk-london-1", "ap-tokyo-1"],
    "Alibaba": ["cn-hangzhou", "ap-southeast-1"],
    "IBM": ["us-south", "eu-de"],
}


def _billing_accounts(ctx, n=500):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "billing_account_id": [f"BA-{rng.choice(PROVIDERS, p=PROV_W)}-{i:06d}" for i in range(1, n + 1)],
        "billing_account_name": [f"{f.company()} Cloud Account" for _ in range(n)],
        "provider": rng.choice(PROVIDERS, size=n, p=PROV_W),
        "billing_currency": weighted_choice(rng, ["USD", "EUR", "GBP", "JPY"], [0.78, 0.12, 0.06, 0.04], n),
        "payer_account_id": [f"PAY-{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "subscription_tier": weighted_choice(rng, ["Enterprise", "Business", "Startup"], [0.40, 0.45, 0.15], n),
        "support_level": weighted_choice(rng, ["Enterprise", "Business", "Developer", "Basic"], [0.25, 0.40, 0.20, 0.15], n),
        "active": rng.random(n) < 0.95,
    })


def _services_table(ctx):
    return pd.DataFrame(SERVICES, columns=["service_name", "provider", "service_category", "service_subcategory"])


def _regions_table(ctx):
    rows = []
    for prov, regs in REGIONS.items():
        for r in regs:
            rows.append((r, prov, r.split("-")[0] if "-" in r else r[:2]))
    return pd.DataFrame(rows, columns=["region_id", "provider", "geography"])


def _invoices(ctx, accounts, n=8_000):
    rng = ctx.rng
    issued = pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "invoice_id": [f"INV-{i:09d}" for i in range(1, n + 1)],
        "billing_account_id": rng.choice(accounts["billing_account_id"].to_numpy(), size=n),
        "invoice_number": [f"{rng.choice(['AWS', 'AZ', 'GCP'])}-{rng.integers(10**8, 10**9)}" for _ in range(n)],
        "billing_period_start": issued.to_period("M").start_time.date,
        "billing_period_end": issued.to_period("M").end_time.date,
        "issue_date": issued.date,
        "due_date": (issued + pd.Timedelta(days=30)).date,
        "subtotal": np.round(rng.lognormal(mean=8, sigma=1.2, size=n), 2),
        "tax_amount": np.round(rng.uniform(0, 0.10, size=n) * rng.lognormal(mean=8, sigma=1.2, size=n), 2),
        "total_amount": np.round(rng.lognormal(mean=8.05, sigma=1.2, size=n), 2),
        "currency": weighted_choice(rng, ["USD", "EUR", "GBP"], [0.80, 0.13, 0.07], n),
        "payment_status": weighted_choice(rng, ["paid", "open", "overdue", "credited"], [0.75, 0.18, 0.05, 0.02], n),
    })


def _charge_records(ctx, accounts, services_df, regions_df, n=300_000):
    """FOCUS-shaped ChargeRecord rows. Primary entity, ~300k."""
    rng = ctx.rng
    svc_idx = rng.integers(0, len(services_df), size=n)
    svc = services_df.iloc[svc_idx]
    provider = svc["provider"].to_numpy()
    region = []
    for p in provider:
        region.append(rng.choice(REGIONS[p]))
    period_start = pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    list_cost = np.round(rng.lognormal(mean=2.0, sigma=2.0, size=n), 4)
    discount = rng.uniform(0, 0.4, size=n)
    eff = np.round(list_cost * (1 - discount), 4)
    return pd.DataFrame({
        "charge_record_id": [f"CHG-{i:011d}" for i in range(1, n + 1)],
        "billing_account_id": rng.choice(accounts["billing_account_id"].to_numpy(), size=n),
        "provider": provider,
        "service_name": svc["service_name"].to_numpy(),
        "service_category": svc["service_category"].to_numpy(),
        "service_subcategory": svc["service_subcategory"].to_numpy(),
        "region_id": region,
        "resource_id": [f"{rng.choice(['i', 'fn', 'sg', 'db'])}-{rng.integers(10**12, 10**13):013x}" for _ in range(n)],
        "resource_type": rng.choice(["VirtualMachine", "Function", "Bucket", "DBInstance", "LoadBalancer", "Cluster", "Volume"], size=n),
        "charge_period_start": period_start,
        "charge_period_end": period_start + pd.Timedelta(hours=1),
        "charge_category": weighted_choice(rng, ["Usage", "Purchase", "Tax", "Adjustment", "Credit"], [0.85, 0.05, 0.05, 0.03, 0.02], n),
        "charge_class": weighted_choice(rng, ["Correction", ""], [0.02, 0.98], n),
        "pricing_unit": rng.choice(["Hours", "GB-Months", "Requests", "GB", "vCPU-Hours"], size=n),
        "pricing_quantity": np.round(rng.gamma(2, 4, size=n), 6),
        "list_unit_price": np.round(rng.uniform(0.001, 1.5, size=n), 6),
        "list_cost": list_cost,
        "billed_cost": eff,
        "effective_cost": eff,
        "billing_currency": weighted_choice(rng, ["USD", "EUR", "GBP"], [0.80, 0.13, 0.07], n),
        "commitment_discount_id": np.where(rng.random(n) < 0.20, [f"COM-{rng.integers(1, 5_000):05d}" for _ in range(n)], None),
        "commitment_discount_category": np.where(rng.random(n) < 0.20, rng.choice(["SavingsPlan", "ReservedInstance", "CommittedUseDiscount"], size=n), None),
        "tag_environment": weighted_choice(rng, ["prod", "staging", "dev", "qa", "untagged"], [0.45, 0.18, 0.18, 0.04, 0.15], n),
        "tag_team": rng.choice(["data", "platform", "ml", "growth", "infra", "security", "sre", "untagged"], size=n),
    })


def _resource_tags(ctx, charges, n_target=80_000):
    rng = ctx.rng
    n = min(n_target, len(charges))
    sub = charges.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "tag_id": [f"TAG-{i:09d}" for i in range(1, n + 1)],
        "resource_id": sub["resource_id"].to_numpy(),
        "tag_key": rng.choice(["Environment", "Team", "CostCenter", "Project", "Owner", "Application"], size=n),
        "tag_value": rng.choice(["prod", "staging", "data", "platform", "ml", "CC1001", "CC1002", "growth", "infra"], size=n),
        "tagged_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s"),
    })


def _commitments(ctx, accounts, n=10_000):
    rng = ctx.rng
    start = pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s")
    term_months = rng.choice([12, 36], size=n, p=[0.65, 0.35])
    return pd.DataFrame({
        "commitment_id": [f"COM-{i:05d}" for i in range(1, n + 1)],
        "billing_account_id": rng.choice(accounts["billing_account_id"].to_numpy(), size=n),
        "commitment_type": weighted_choice(rng, ["SavingsPlan", "ReservedInstance", "CommittedUseDiscount"], [0.45, 0.40, 0.15], n),
        "provider": rng.choice(PROVIDERS, size=n, p=PROV_W),
        "service_name": rng.choice([s[0] for s in SERVICES], size=n),
        "term_months": term_months,
        "start_date": start.date,
        "end_date": (start + pd.to_timedelta(term_months * 30, unit="D")).date,
        "hourly_commitment_usd": np.round(rng.uniform(1, 200, size=n), 2),
        "upfront_payment_usd": np.round(rng.choice([0, 5_000, 25_000, 100_000], size=n, p=[0.70, 0.15, 0.10, 0.05]), 2),
        "utilization_pct": np.round(rng.beta(7, 2, size=n), 3),
        "coverage_pct": np.round(rng.beta(4, 2, size=n), 3),
    })


def _allocations(ctx, accounts, n=20_000):
    rng = ctx.rng
    period_start = pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").to_period("M").start_time
    return pd.DataFrame({
        "allocation_id": [f"ALC-{i:08d}" for i in range(1, n + 1)],
        "billing_account_id": rng.choice(accounts["billing_account_id"].to_numpy(), size=n),
        "cost_center": rng.choice([f"CC{i:04d}" for i in range(1001, 1100)], size=n),
        "department": rng.choice(["Engineering", "Data", "ML", "Marketing", "Finance", "Sales", "Ops"], size=n),
        "period_start": period_start.date,
        "period_end": (period_start + pd.offsets.MonthEnd(0)).date,
        "allocated_amount_usd": np.round(rng.lognormal(mean=8, sigma=1.5, size=n), 2),
        "allocation_method": weighted_choice(rng, ["TagBased", "Proportional", "Equal", "Manual"], [0.55, 0.25, 0.10, 0.10], n),
    })


def _budgets(ctx, accounts, n=4_000):
    rng = ctx.rng
    period_start = pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").to_period("M").start_time
    amount = np.round(rng.lognormal(mean=10, sigma=1.2, size=n), 2)
    actual = np.round(amount * rng.uniform(0.5, 1.4, size=n), 2)
    return pd.DataFrame({
        "budget_id": [f"BUD-{i:06d}" for i in range(1, n + 1)],
        "billing_account_id": rng.choice(accounts["billing_account_id"].to_numpy(), size=n),
        "name": [f"Budget Q{rng.integers(1, 5)} CC{rng.integers(1001, 1100):04d}" for _ in range(n)],
        "period_start": period_start.date,
        "period_end": (period_start + pd.offsets.MonthEnd(0)).date,
        "budgeted_amount_usd": amount,
        "actual_spend_usd": actual,
        "forecast_amount_usd": np.round(actual * rng.uniform(0.95, 1.15, size=n), 2),
        "alert_threshold_pct": rng.choice([50, 75, 90, 100], size=n, p=[0.10, 0.30, 0.40, 0.20]),
        "alert_triggered": actual > amount,
        "owner_email": [f"finops+{rng.integers(1000, 9999)}@example.com" for _ in range(n)],
    })


def generate(seed=42):
    ctx = make_context(seed)
    accounts = _billing_accounts(ctx)
    services = _services_table(ctx)
    regions = _regions_table(ctx)
    invoices = _invoices(ctx, accounts)
    charges = _charge_records(ctx, accounts, services, regions)
    tags = _resource_tags(ctx, charges)
    commitments = _commitments(ctx, accounts)
    allocations = _allocations(ctx, accounts)
    budgets = _budgets(ctx, accounts)
    tables = {
        "billing_account": accounts,
        "service": services,
        "region": regions,
        "invoice": invoices,
        "charge_record": charges,
        "resource_tag": tags,
        "commitment": commitments,
        "allocation": allocations,
        "budget": budgets,
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
