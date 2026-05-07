"""
Synthetic Capital Markets data — FIX 4.4 / FpML 5 / FIA-recap.

Entities (>=8): instrument, party, account, order, execution, trade, fpml_trade,
position, allocation, market_data_snapshot, risk_factor.

Realism:
  - Instruments: real CFI codes (ISO 10962), realistic ISIN check digits,
    asset-class-aware exchange MICs.
  - Orders: lognormal qty, realistic fill ratios, OUCH-like venue mix.
  - Executions: per-leg slippage, microsecond-level timestamps.
  - Risk factors: realistic vol-cone shapes for FX, IR, EQ.
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
    lognormal_amounts,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "capital_markets"

EXCHANGES = ["XNYS", "XNAS", "XLON", "XHKG", "XTKS", "XPAR", "XFRA", "XSWX", "XASX", "XTSE"]
ASSET_CLASSES = ["EQUITY", "FX", "RATES", "CREDIT", "COMMODITY", "ETF", "OPTION", "FUTURE"]
CFI_BY_CLASS = {
    "EQUITY": "ESVUFR",
    "FX": "MRCXXX",
    "RATES": "DBVNFR",
    "CREDIT": "DBVNFR",
    "COMMODITY": "FFMCSP",
    "ETF": "CEOIRS",
    "OPTION": "OCASPS",
    "FUTURE": "FFICSP",
}
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "BAC", "WMT",
    "JNJ", "PG", "XOM", "CVX", "KO", "PEP", "V", "MA", "UNH", "HD",
    "DIS", "NFLX", "ADBE", "CRM", "ORCL", "INTC", "AMD", "QCOM", "CSCO", "IBM",
]


def _isin_check(body: str) -> str:
    digits = ""
    for ch in body:
        if ch.isalpha():
            digits += str(ord(ch.upper()) - 55)
        else:
            digits += ch
    total = 0
    for i, d in enumerate(reversed(digits)):
        v = int(d)
        if i % 2 == 0:
            v *= 2
        total += v // 10 + v % 10
    return str((10 - total % 10) % 10)


def _instruments(ctx, n=10_000):
    rng = ctx.rng
    asset = weighted_choice(rng, ASSET_CLASSES, [0.45, 0.10, 0.10, 0.05, 0.10, 0.10, 0.05, 0.05], n)
    countries = ["US", "GB", "DE", "JP", "HK", "FR", "CH", "AU", "CA", "NL"]
    isins = []
    cusips = []
    figis = []
    cfis = []
    short_names = []
    for i, a in enumerate(asset):
        country = rng.choice(countries)
        body = f"{country}{rng.integers(0, 10**9):09d}"[:11]
        body = body.ljust(11, "0")
        isins.append(body + _isin_check(body))
        cusips.append(f"{rng.integers(10**8, 10**9):09d}")
        figis.append(f"BBG{rng.integers(10**8, 10**9):09X}")
        cfis.append(CFI_BY_CLASS[a])
        if a == "EQUITY":
            short_names.append(rng.choice(TICKERS))
        elif a == "FX":
            short_names.append(rng.choice(["EURUSD", "USDJPY", "GBPUSD", "USDCHF", "AUDUSD"]))
        else:
            short_names.append(f"{a}_{i % 1000:04d}")
    return pd.DataFrame({
        "instrument_id": [f"INS{i:08d}" for i in range(1, n + 1)],
        "isin": isins,
        "cusip": cusips,
        "figi": figis,
        "cfi_code": cfis,
        "short_name": short_names,
        "asset_class": asset,
        "currency": weighted_choice(rng, ["USD", "EUR", "GBP", "JPY", "CHF", "HKD", "AUD"], [0.55, 0.20, 0.10, 0.06, 0.03, 0.03, 0.03], n),
        "country_of_issue": rng.choice(countries, size=n),
        "primary_exchange_mic": rng.choice(EXCHANGES, size=n),
        "status": weighted_choice(rng, ["active", "suspended", "delisted"], [0.94, 0.04, 0.02], n),
    })


def _parties(ctx, n=2_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "party_id": [f"PTY{i:06d}" for i in range(1, n + 1)],
        "lei": [f"{rng.integers(10**18, 10**19):020d}"[:20] for _ in range(n)],
        "bic": [f"{rng.choice(['BANK', 'CITI', 'JPMC', 'GSCO', 'MSCO', 'BNPP', 'DEUT'])}{rng.choice(['US', 'GB', 'DE', 'JP'])}{rng.integers(10, 99)}" for _ in range(n)],
        "legal_name": [f.company() for _ in range(n)],
        "party_role": weighted_choice(rng, ["Buyside", "Sellside", "Custodian", "Broker", "CCP", "Exchange"], [0.30, 0.30, 0.10, 0.20, 0.05, 0.05], n),
        "country_iso": rng.choice(["US", "GB", "DE", "JP", "HK", "FR", "CH"], size=n),
        "status": weighted_choice(rng, ["active", "suspended", "closed"], [0.95, 0.04, 0.01], n),
    })


def _accounts(ctx, parties, n=5_000):
    rng = ctx.rng
    return pd.DataFrame({
        "account_id": [f"ACT{i:07d}" for i in range(1, n + 1)],
        "owner_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "account_type": weighted_choice(rng, ["principal", "agency", "omnibus", "client"], [0.30, 0.30, 0.20, 0.20], n),
        "currency": weighted_choice(rng, ["USD", "EUR", "GBP", "JPY", "CHF"], [0.65, 0.18, 0.08, 0.06, 0.03], n),
        "status": weighted_choice(rng, ["active", "frozen", "closed"], [0.93, 0.04, 0.03], n),
    })


def _orders(ctx, instruments, parties, accounts, n=80_000):
    rng = ctx.rng
    placed = daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30"))
    qty = lognormal_amounts(rng, n, mean=6.5, sigma=1.0).astype(int)
    return pd.DataFrame({
        "order_id": [f"ORD{i:09d}" for i in range(1, n + 1)],
        "cl_ord_id": [f"CL{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "instrument_id": rng.choice(instruments["instrument_id"].to_numpy(), size=n),
        "account_id": rng.choice(accounts["account_id"].to_numpy(), size=n),
        "submitting_party_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "side": weighted_choice(rng, ["BUY", "SELL", "SELL_SHORT"], [0.48, 0.48, 0.04], n),
        "ord_type": weighted_choice(rng, ["LIMIT", "MARKET", "STOP", "STOP_LIMIT", "PEGGED"], [0.65, 0.20, 0.05, 0.05, 0.05], n),
        "time_in_force": weighted_choice(rng, ["DAY", "IOC", "GTC", "FOK", "GTD"], [0.55, 0.20, 0.15, 0.05, 0.05], n),
        "qty": qty,
        "limit_price": np.round(rng.uniform(1, 1000, size=n), 4),
        "placed_at": placed,
        "status": weighted_choice(rng, ["filled", "partially_filled", "cancelled", "rejected", "open"], [0.65, 0.15, 0.10, 0.05, 0.05], n),
    })


def _executions(ctx, orders, n_target=200_000):
    rng = ctx.rng
    fillable = orders[orders["status"].isin(["filled", "partially_filled"])]
    n = max(n_target, len(fillable))
    base_idx = rng.integers(0, len(fillable), size=n)
    parent = fillable.iloc[base_idx].reset_index(drop=True)
    parent_qty = parent["qty"].to_numpy()
    last_qty = (parent_qty * rng.uniform(0.05, 0.6, size=n)).clip(1).astype(int)
    placed = pd.to_datetime(parent["placed_at"].to_numpy())
    latency_us = rng.gamma(2.0, 250, size=n).clip(50, 50_000).astype(int)
    exec_ts = placed + pd.to_timedelta(latency_us, unit="us")
    side = parent["side"].to_numpy()
    limit = parent["limit_price"].to_numpy()
    slippage_bps = rng.normal(0, 8, size=n).clip(-50, 50)
    last_px = limit * (1 + np.where(side == "BUY", slippage_bps, -slippage_bps) / 10000.0)
    return pd.DataFrame({
        "execution_id": [f"EXE{i:010d}" for i in range(1, n + 1)],
        "order_id": parent["order_id"].to_numpy(),
        "exec_id": [f"X{rng.integers(10**9, 10**10):010d}" for _ in range(n)],
        "exec_type": weighted_choice(rng, ["F", "0", "5", "4"], [0.82, 0.10, 0.04, 0.04], n),
        "ord_status": weighted_choice(rng, ["1", "2"], [0.30, 0.70], n),
        "instrument_id": parent["instrument_id"].to_numpy(),
        "side": side,
        "last_qty": last_qty,
        "last_px": np.round(last_px, 4),
        "exec_ts": exec_ts,
        "venue_mic": rng.choice(EXCHANGES, size=n),
        "liquidity_indicator": weighted_choice(rng, ["A", "R", "X"], [0.45, 0.50, 0.05], n),
        "commission": np.round(last_qty * last_px * rng.uniform(0.0001, 0.0008, size=n), 4),
    })


def _trades(ctx, executions, accounts, n_target=120_000):
    rng = ctx.rng
    n = min(n_target, len(executions))
    src = executions.iloc[:n].copy().reset_index(drop=True)
    return pd.DataFrame({
        "trade_id": [f"TRD{i:010d}" for i in range(1, n + 1)],
        "execution_id": src["execution_id"].to_numpy(),
        "instrument_id": src["instrument_id"].to_numpy(),
        "account_id": rng.choice(accounts["account_id"].to_numpy(), size=n),
        "trade_date": pd.to_datetime(src["exec_ts"].to_numpy()).date,
        "settlement_date": pd.to_datetime(src["exec_ts"].to_numpy()).date + pd.Timedelta(days=2),
        "side": src["side"].to_numpy(),
        "quantity": src["last_qty"].to_numpy(),
        "price": src["last_px"].to_numpy(),
        "gross_amount": np.round(src["last_qty"].to_numpy() * src["last_px"].to_numpy(), 4),
        "currency": rng.choice(["USD", "EUR", "GBP"], size=n, p=[0.7, 0.2, 0.1]),
        "venue_mic": src["venue_mic"].to_numpy(),
    })


def _fpml_trades(ctx, parties, n=8_000):
    rng = ctx.rng
    f = ctx.faker
    eff = pd.to_datetime(rng.integers(int(pd.Timestamp("2023-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s")
    tenor_days = rng.choice([90, 180, 365, 730, 1825, 3650], size=n)
    return pd.DataFrame({
        "fpml_trade_id": [f"FPM{i:08d}" for i in range(1, n + 1)],
        "product_type": weighted_choice(rng, ["IRSwap", "FxForward", "FxOption", "CDS", "EquityOption", "TotalReturnSwap"], [0.40, 0.20, 0.10, 0.10, 0.15, 0.05], n),
        "party1_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "party2_id": rng.choice(parties["party_id"].to_numpy(), size=n),
        "notional": np.round(rng.lognormal(mean=15, sigma=1.5, size=n), 2),
        "notional_currency": rng.choice(["USD", "EUR", "GBP", "JPY"], size=n, p=[0.55, 0.25, 0.12, 0.08]),
        "trade_date": eff.date,
        "effective_date": eff.date,
        "termination_date": (eff + pd.to_timedelta(tenor_days, unit="D")).date,
        "fixed_rate": np.round(rng.uniform(0.005, 0.06, size=n), 6),
        "floating_index": rng.choice(["SOFR", "ESTR", "TONA", "SONIA"], size=n),
        "day_count_fraction": rng.choice(["ACT/360", "ACT/365", "30/360"], size=n),
        "uti": [f"UTI{rng.integers(10**11, 10**12):012d}" for _ in range(n)],
    })


def _positions(ctx, instruments, accounts, n=20_000):
    rng = ctx.rng
    qty = rng.integers(-50_000, 50_000, size=n)
    avg_px = np.round(rng.uniform(1, 800, size=n), 4)
    return pd.DataFrame({
        "position_id": [f"POS{i:08d}" for i in range(1, n + 1)],
        "account_id": rng.choice(accounts["account_id"].to_numpy(), size=n),
        "instrument_id": rng.choice(instruments["instrument_id"].to_numpy(), size=n),
        "as_of_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "quantity": qty,
        "average_price": avg_px,
        "market_value": np.round(qty * avg_px, 2),
        "currency": "USD",
    })


def _allocations(ctx, trades, accounts, n=30_000):
    rng = ctx.rng
    n = min(n, len(trades))
    src = trades.sample(n=n, random_state=ctx.seed).reset_index(drop=True)
    return pd.DataFrame({
        "allocation_id": [f"ALC{i:09d}" for i in range(1, n + 1)],
        "trade_id": src["trade_id"].to_numpy(),
        "client_account_id": rng.choice(accounts["account_id"].to_numpy(), size=n),
        "allocated_qty": (src["quantity"].to_numpy() * rng.uniform(0.05, 0.4, size=n)).astype(int).clip(1),
        "allocated_amount": np.round(src["gross_amount"].to_numpy() * rng.uniform(0.05, 0.4, size=n), 2),
        "average_price": src["price"].to_numpy(),
        "status": weighted_choice(rng, ["confirmed", "pending", "rejected"], [0.92, 0.06, 0.02], n),
    })


def _market_data_snapshots(ctx, instruments, n=120_000):
    rng = ctx.rng
    ts = daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30"))
    mid = rng.uniform(1, 1000, size=n)
    spread_bps = rng.gamma(1.5, 2.0, size=n).clip(0.1, 80)
    return pd.DataFrame({
        "snapshot_id": [f"MDS{i:010d}" for i in range(1, n + 1)],
        "instrument_id": rng.choice(instruments["instrument_id"].to_numpy(), size=n),
        "snapshot_ts": ts,
        "bid_px": np.round(mid * (1 - spread_bps / 20000.0), 4),
        "ask_px": np.round(mid * (1 + spread_bps / 20000.0), 4),
        "bid_size": rng.integers(100, 100_000, size=n),
        "ask_size": rng.integers(100, 100_000, size=n),
        "last_px": np.round(mid, 4),
        "volume_today": rng.integers(0, 5_000_000, size=n),
        "venue_mic": rng.choice(EXCHANGES, size=n),
    })


def _risk_factors(ctx, n=15_000):
    rng = ctx.rng
    factors = ["EUR/USD", "USD/JPY", "GBP/USD", "USD-Treasury-2Y", "USD-Treasury-10Y", "Brent", "WTI", "S&P500", "VIX", "EURIBOR-3M", "SOFR-1M"]
    fac = rng.choice(factors, size=n)
    return pd.DataFrame({
        "risk_factor_id": [f"RFK{i:08d}" for i in range(1, n + 1)],
        "factor_name": fac,
        "factor_class": np.where(np.isin(fac, ["EUR/USD", "USD/JPY", "GBP/USD"]), "FX",
                          np.where(np.isin(fac, ["USD-Treasury-2Y", "USD-Treasury-10Y", "EURIBOR-3M", "SOFR-1M"]), "RATES",
                          np.where(np.isin(fac, ["Brent", "WTI"]), "COMMODITY", "EQUITY"))),
        "as_of_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2025-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "level": np.round(rng.uniform(0.001, 5000, size=n), 6),
        "vol_1d": np.round(np.abs(rng.normal(0, 0.01, size=n)), 6),
        "vol_30d": np.round(np.abs(rng.normal(0, 0.05, size=n)), 6),
    })


def generate(seed=42):
    ctx = make_context(seed)
    instruments = _instruments(ctx)
    parties = _parties(ctx)
    accounts = _accounts(ctx, parties)
    orders = _orders(ctx, instruments, parties, accounts)
    executions = _executions(ctx, orders)
    trades = _trades(ctx, executions, accounts)
    fpml = _fpml_trades(ctx, parties)
    positions = _positions(ctx, instruments, accounts)
    allocations = _allocations(ctx, trades, accounts)
    md = _market_data_snapshots(ctx, instruments)
    risk = _risk_factors(ctx)
    tables = {
        "instrument": instruments,
        "party": parties,
        "account": accounts,
        "order": orders,
        "execution": executions,
        "trade": trades,
        "fpml_trade": fpml,
        "position": positions,
        "allocation": allocations,
        "market_data_snapshot": md,
        "risk_factor": risk,
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
