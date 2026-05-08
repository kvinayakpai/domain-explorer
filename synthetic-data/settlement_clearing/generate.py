"""
Synthetic Settlement & Clearing data — ISO 20022 sese.* / semt.* / colr.*.

Entities (>=8): party, instrument, trade, settlement_instruction,
matching_status, settlement_confirmation, failed_settlement, margin_call,
collateral_movement, reconciliation_break, cns_obligation, buyin.

Realism:
  - Real CSDR-style fail rate (~3-5% in equities, lower in govies).
  - Match rate by T+1 ~92-96%.
  - Status codes follow ISO 20022 Status Reason values: PEND, MACH, NMAT, CANC.
  - Buyin events are rare; CSDR cash penalties applied.
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

SUBDOMAIN = "settlement_clearing"


def _parties(ctx, n=2_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "party_id": [f"PTY{i:06d}" for i in range(1, n + 1)],
        "lei": [f"{rng.integers(0, 10**18):018d}{rng.integers(0, 100):02d}" for _ in range(n)],
        "bic": [f"{rng.choice(['BANK', 'CITI', 'JPMC', 'GSCO', 'MSCO', 'BNPP', 'DEUT', 'BARC', 'HSBC'])}{rng.choice(['US', 'GB', 'DE', 'JP', 'FR'])}{rng.integers(10, 99)}" for _ in range(n)],
        "legal_name": [f.company() for _ in range(n)],
        "party_role": weighted_choice(rng, ["AccountOwner", "AccountServicer", "CSD", "CCP", "CashAgent", "SettlementAgent"], [0.40, 0.25, 0.10, 0.05, 0.10, 0.10], n),
        "country_iso": rng.choice(["US", "GB", "DE", "JP", "FR", "CH", "HK", "SG"], size=n),
        "status": weighted_choice(rng, ["active", "suspended", "closed"], [0.95, 0.03, 0.02], n),
    })


def _instruments(ctx, n=4_000):
    rng = ctx.rng
    return pd.DataFrame({
        "instrument_id": [f"INS{i:07d}" for i in range(1, n + 1)],
        "isin": [f"US{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "cusip": [f"{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "cfi_code": rng.choice(["ESVUFR", "DBVNFR", "EFVUFR", "FFICSP"], size=n),
        "short_name": [f"SEC{i:05d}" for i in range(1, n + 1)],
        "currency": weighted_choice(rng, ["USD", "EUR", "GBP", "JPY", "CHF"], [0.55, 0.25, 0.10, 0.07, 0.03], n),
        "country_of_issue": rng.choice(["US", "GB", "DE", "JP", "FR"], size=n),
        "maturity_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2026-01-01").timestamp()), int(pd.Timestamp("2055-12-31").timestamp()), size=n), unit="s").date,
        "status": weighted_choice(rng, ["active", "matured", "delisted"], [0.90, 0.07, 0.03], n),
    })


def _trades(ctx, instruments, parties, n=20_000):
    rng = ctx.rng
    trade_date = pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-25").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "trade_id": [f"TRD{i:08d}" for i in range(1, n + 1)],
        "instrument_id": rng.choice(instruments["instrument_id"].to_numpy(), size=n),
        "account_owner_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "counterparty_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "side": weighted_choice(rng, ["BUYI", "SELL"], [0.50, 0.50], n),
        "quantity": np.round(rng.lognormal(mean=7, sigma=1.2, size=n), 4),
        "trade_price": np.round(rng.uniform(1, 1000, size=n), 6),
        "trade_date": trade_date.date,
        "settlement_date": (trade_date + pd.Timedelta(days=2)).date,
        "clearing_status": weighted_choice(rng, ["Cleared", "PendingClearing", "Bilateral"], [0.80, 0.10, 0.10], n),
        "ccp_id": [f"CCP{rng.integers(1, 10):03d}" for _ in range(n)],
        "csd_id": [f"CSD{rng.integers(1, 10):03d}" for _ in range(n)],
    })


def _settlement_instructions(ctx, trades, parties, n_target=20_000):
    """Primary entity — settlement instructions (ISO 20022 sese.023)."""
    rng = ctx.rng
    n = max(n_target, len(trades))
    src = trades.sample(n=n, replace=(n > len(trades)), random_state=ctx.seed).reset_index(drop=True)
    qty = src["quantity"].to_numpy()
    px = src["trade_price"].to_numpy()
    return pd.DataFrame({
        "ssi_id": [f"SSI{i:09d}" for i in range(1, n + 1)],
        "trade_id": src["trade_id"].to_numpy(),
        "account_owner_party_id": src["account_owner_party_id"].to_numpy(),
        "safekeeping_account_id": [f"SAFE{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "cash_account_id": [f"CASH{rng.integers(10**6, 10**7):07d}" for _ in range(n)],
        "instrument_id": src["instrument_id"].to_numpy(),
        "settlement_quantity": qty,
        "settlement_amount": np.round(qty * px, 4),
        "settlement_currency": rng.choice(["USD", "EUR", "GBP"], size=n, p=[0.65, 0.25, 0.10]),
        "trade_date": src["trade_date"].to_numpy(),
        "settlement_date": src["settlement_date"].to_numpy(),
        "delivery_type": rng.choice(["DELI", "RECE"], size=n),
        "payment_type": rng.choice(["APMT", "FREE"], size=n, p=[0.95, 0.05]),
        "created_at": pd.to_datetime(src["trade_date"].to_numpy()) + pd.to_timedelta(rng.integers(1, 240, size=n), unit="m"),
        "status": weighted_choice(rng, ["Settled", "Pending", "Failed", "Cancelled"], [0.91, 0.04, 0.04, 0.01], n),
    })


def _matching_status(ctx, ssi, n_target=40_000):
    rng = ctx.rng
    n = min(n_target, len(ssi) * 3)
    src = ssi.sample(n=n, replace=(n > len(ssi)), random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "matching_status_id": [f"MS{i:09d}" for i in range(1, n + 1)],
        "ssi_id": src["ssi_id"].to_numpy(),
        "status_code": weighted_choice(rng, ["MACH", "NMAT", "PEND", "CANC"], [0.85, 0.07, 0.06, 0.02], n),
        "status_ts": pd.to_datetime(src["created_at"].to_numpy()) + pd.to_timedelta(rng.integers(1, 1440, size=n), unit="m"),
        "reason_code": rng.choice(["", "DSEC", "DDAT", "DPRC", "DQUA", "MISS", "ADEA"], size=n),
        "matched_party_id": rng.choice(["MATCHED", "UNMATCHED"], size=n, p=[0.93, 0.07]),
    })


def _settlement_confirmation(ctx, ssi, n_target=18_000):
    rng = ctx.rng
    settled = ssi[ssi["status"] == "Settled"]
    n = min(n_target, len(settled))
    src = settled.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "confirmation_id": [f"SC{i:09d}" for i in range(1, n + 1)],
        "ssi_id": src["ssi_id"].to_numpy(),
        "trade_id": src["trade_id"].to_numpy(),
        "settlement_ts": pd.to_datetime(src["created_at"].to_numpy()) + pd.to_timedelta(rng.integers(1, 1440 * 3, size=n), unit="m"),
        "settled_quantity": src["settlement_quantity"].to_numpy(),
        "settled_amount": src["settlement_amount"].to_numpy(),
        "settled_currency": src["settlement_currency"].to_numpy(),
        "delivery_indicator": rng.choice(["DELI", "RECE"], size=n),
        "csd_id": [f"CSD{rng.integers(1, 10):03d}" for _ in range(n)],
    })


def _failed_settlement(ctx, ssi, n_target=2_000):
    rng = ctx.rng
    failed = ssi[ssi["status"] == "Failed"]
    n = min(n_target, len(failed))
    if n == 0:
        return pd.DataFrame(columns=["failure_id", "ssi_id", "fail_reason", "failed_at", "estimated_resolution_date", "csdr_penalty_amount", "status"])
    src = failed.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "failure_id": [f"FAIL{i:08d}" for i in range(1, n + 1)],
        "ssi_id": src["ssi_id"].to_numpy(),
        "fail_reason": weighted_choice(rng, ["LackOfSecurities", "LackOfCash", "MismatchedInstruction", "CSDOperationalIssue", "OnHold", "PartialSettlement"], [0.45, 0.25, 0.15, 0.05, 0.05, 0.05], n),
        "failed_at": pd.to_datetime(src["created_at"].to_numpy()) + pd.to_timedelta(rng.integers(1, 1440 * 2, size=n), unit="m"),
        "estimated_resolution_date": (pd.to_datetime(src["settlement_date"]) + pd.to_timedelta(rng.integers(1, 10, size=n), unit="D")).dt.date,
        "csdr_penalty_amount": np.round(src["settlement_amount"].to_numpy() * rng.uniform(0.0001, 0.0005, size=n), 2),
        "status": weighted_choice(rng, ["UnderInvestigation", "Resolved", "BuyinTriggered"], [0.40, 0.55, 0.05], n),
    })


def _margin_call(ctx, parties, n=12_000):
    rng = ctx.rng
    issued = pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "margin_call_id": [f"MC{i:08d}" for i in range(1, n + 1)],
        "calling_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "called_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "call_type": weighted_choice(rng, ["VariationMargin", "InitialMargin", "DefaultFundContribution"], [0.78, 0.18, 0.04], n),
        "call_amount": np.round(rng.lognormal(mean=14, sigma=1.5, size=n), 2),
        "call_currency": rng.choice(["USD", "EUR", "GBP"], size=n, p=[0.55, 0.30, 0.15]),
        "issued_at": issued,
        "due_at": issued + pd.to_timedelta(rng.integers(2, 24, size=n), unit="h"),
        "status": weighted_choice(rng, ["Issued", "Acknowledged", "Disputed", "Settled", "OverdueOpen"], [0.05, 0.10, 0.04, 0.78, 0.03], n),
    })


def _collateral_movement(ctx, parties, n=20_000):
    rng = ctx.rng
    return pd.DataFrame({
        "collateral_movement_id": [f"COL{i:09d}" for i in range(1, n + 1)],
        "collateral_giver_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "collateral_taker_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "direction": weighted_choice(rng, ["Pledge", "Return", "Substitution"], [0.55, 0.40, 0.05], n),
        "collateral_type": weighted_choice(rng, ["Cash", "Government Bond", "Corporate Bond", "Equity", "Cash Equivalent"], [0.40, 0.30, 0.15, 0.10, 0.05], n),
        "quantity": np.round(rng.lognormal(mean=7, sigma=1.2, size=n), 2),
        "market_value": np.round(rng.lognormal(mean=14, sigma=1.0, size=n), 2),
        "haircut_pct": np.round(rng.uniform(0.0, 0.20, size=n), 4),
        "post_haircut_value": np.round(rng.lognormal(mean=13.8, sigma=1.0, size=n), 2),
        "currency": rng.choice(["USD", "EUR", "GBP"], size=n, p=[0.55, 0.30, 0.15]),
        "movement_ts": pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s"),
        "status": weighted_choice(rng, ["Settled", "Pending", "Failed"], [0.93, 0.05, 0.02], n),
    })


def _reconciliation_break(ctx, n=10_000):
    rng = ctx.rng
    detected = pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "break_id": [f"BRK{i:08d}" for i in range(1, n + 1)],
        "recon_type": weighted_choice(rng, ["Position", "Cash", "Trade", "Stock-Loan", "FX-PvP"], [0.40, 0.25, 0.15, 0.10, 0.10], n),
        "side_a_system": rng.choice(["GoldenSrc", "Murex", "BackOffice", "GMI", "Calypso"], size=n),
        "side_b_system": rng.choice(["FedFunds", "DTCC", "Bloomberg", "Custodian", "CCP"], size=n),
        "instrument_id": [f"INS{rng.integers(1, 4_000):07d}" for _ in range(n)],
        "qty_diff": np.round(rng.normal(0, 100, size=n), 2),
        "amount_diff": np.round(rng.normal(0, 50_000, size=n), 2),
        "currency": rng.choice(["USD", "EUR", "GBP"], size=n, p=[0.6, 0.25, 0.15]),
        "detected_at": detected,
        "status": weighted_choice(rng, ["Open", "InProgress", "Aged", "Resolved", "WrittenOff"], [0.10, 0.20, 0.10, 0.55, 0.05], n),
        "owner_team": rng.choice(["MO-Equity", "MO-FX", "MO-Fixed-Income", "Treasury", "BackOffice"], size=n),
        "aged_days": rng.integers(0, 60, size=n),
    })


def _cns_obligation(ctx, instruments, parties, n=8_000):
    """DTCC NSCC Continuous Net Settlement obligations."""
    rng = ctx.rng
    long_pos = np.round(rng.lognormal(mean=7, sigma=1.5, size=n), 2)
    short_pos = np.round(rng.lognormal(mean=7, sigma=1.5, size=n), 2)
    return pd.DataFrame({
        "cns_id": [f"CNS{i:08d}" for i in range(1, n + 1)],
        "as_of_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "participant_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "instrument_id": rng.choice(instruments["instrument_id"].to_numpy(), size=n),
        "long_position_qty": long_pos,
        "short_position_qty": short_pos,
        "net_position_qty": np.round(long_pos - short_pos, 2),
        "net_position_amount": np.round((long_pos - short_pos) * rng.uniform(1, 200, size=n), 2),
        "currency": "USD",
        "settlement_date": (pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s") + pd.Timedelta(days=2)).date,
    })


def _buyin(ctx, n=600):
    rng = ctx.rng
    executed = pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    return pd.DataFrame({
        "buyin_id": [f"BIN{i:06d}" for i in range(1, n + 1)],
        "ssi_id": [f"SSI{rng.integers(1, 19_000):09d}" for _ in range(n)],
        "trigger_reason": weighted_choice(rng, ["CSDR-mandatory", "Discretionary", "Market-rules"], [0.55, 0.35, 0.10], n),
        "instrument_id": [f"INS{rng.integers(1, 4_000):07d}" for _ in range(n)],
        "quantity": np.round(rng.lognormal(mean=6, sigma=1.0, size=n), 2),
        "execution_price": np.round(rng.uniform(1, 1000, size=n), 4),
        "executed_at": executed,
        "agent_party_id": [f"PTY{rng.integers(1, 2_000):06d}" for _ in range(n)],
        "settled_at": executed + pd.to_timedelta(rng.integers(1, 5, size=n), unit="D"),
        "cost_to_failing_party": np.round(rng.lognormal(mean=8, sigma=1.0, size=n), 2),
    })


def generate(seed=42):
    ctx = make_context(seed)
    parties = _parties(ctx)
    instruments = _instruments(ctx)
    trades = _trades(ctx, instruments, parties)
    ssi = _settlement_instructions(ctx, trades, parties)
    matching = _matching_status(ctx, ssi)
    confirms = _settlement_confirmation(ctx, ssi)
    fails = _failed_settlement(ctx, ssi)
    mc = _margin_call(ctx, parties)
    coll = _collateral_movement(ctx, parties)
    breaks = _reconciliation_break(ctx)
    cns = _cns_obligation(ctx, instruments, parties)
    buyins = _buyin(ctx)
    tables = {
        "party": parties,
        "instrument": instruments,
        "trade": trades,
        "settlement_instruction": ssi,
        "matching_status": matching,
        "settlement_confirmation": confirms,
        "failed_settlement": fails,
        "margin_call": mc,
        "collateral_movement": coll,
        "reconciliation_break": breaks,
        "cns_obligation": cns,
        "buyin": buyins,
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
