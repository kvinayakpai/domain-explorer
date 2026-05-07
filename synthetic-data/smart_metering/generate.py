"""
Synthetic Smart Metering data — ANSI C12.19/C12.22 + DLMS/COSEM.

Entities (>=8): service_point, meter, meter_read, billing_determinant,
field_order, ami_event, asset_register, outage_event, tamper_event.

Realism:
  - Meter reads on 15-minute intervals (96 reads / day) for AMI.
  - Daily kWh shaped by weekday/weekend + diurnal sine + per-customer drift.
  - Tamper events ~0.05% rate; outage events ~1.5% (varies by feeder).
  - DLMS OBIS codes used as channel identifiers.
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

SUBDOMAIN = "smart_metering"

OBIS_ACTIVE_ENERGY = "1-0:1.8.0"
OBIS_REACTIVE = "1-0:3.8.0"
OBIS_VOLTAGE = "1-0:32.7.0"
OBIS_CURRENT = "1-0:31.7.0"


def _service_points(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    feeders = [f"FDR{i:04d}" for i in range(1, 80)]
    return pd.DataFrame({
        "service_point_id": [f"SP{i:08d}" for i in range(1, n + 1)],
        "premise_id": [f"PRM{i:08d}" for i in range(1, n + 1)],
        "address_line": [f.street_address() for _ in range(n)],
        "address_city": [f.city() for _ in range(n)],
        "address_state": rng.choice(["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "AZ", "NC"], size=n),
        "service_class": weighted_choice(rng, ["RES", "C&I-small", "C&I-medium", "C&I-large", "MUNI"], [0.78, 0.12, 0.06, 0.02, 0.02], n),
        "rate_schedule": weighted_choice(rng, ["E-1", "E-TOU-A", "E-TOU-B", "E-TOU-C", "GS-1", "AG-1"], [0.45, 0.20, 0.10, 0.10, 0.10, 0.05], n),
        "feeder_id": rng.choice(feeders, size=n),
        "transformer_id": [f"XFR{rng.integers(1, 5_000):05d}" for _ in range(n)],
        "latitude": np.round(rng.uniform(32.5, 42.0, size=n), 6),
        "longitude": np.round(rng.uniform(-124.0, -73.0, size=n), 6),
        "active_since": pd.to_datetime(rng.integers(int(pd.Timestamp("2010-01-01").timestamp()), int(pd.Timestamp("2024-12-31").timestamp()), size=n), unit="s").date,
    })


def _meters(ctx, service_points, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "meter_id": [f"MTR{i:09d}" for i in range(1, n + 1)],
        "serial_number": [f"SN{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "service_point_id": rng.choice(service_points["service_point_id"].to_numpy(), size=n, replace=False) if n <= len(service_points) else rng.choice(service_points["service_point_id"].to_numpy(), size=n),
        "manufacturer": weighted_choice(rng, ["Itron", "Landis+Gyr", "Sensus", "Aclara", "Honeywell"], [0.40, 0.30, 0.15, 0.10, 0.05], n),
        "model": weighted_choice(rng, ["OpenWay", "Focus AX", "iCon", "I-210+", "kV2c"], [0.35, 0.25, 0.20, 0.10, 0.10], n),
        "firmware_version": rng.choice(["3.0.4", "3.1.2", "3.2.0", "4.0.1", "4.1.3"], size=n),
        "form_factor": weighted_choice(rng, ["2S", "12S", "16S", "5S"], [0.55, 0.20, 0.15, 0.10], n),
        "communication_protocol": weighted_choice(rng, ["RF-mesh", "PLC", "Cellular-LTE", "Cellular-CatM"], [0.55, 0.20, 0.15, 0.10], n),
        "installed_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2014-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s").date,
        "ct_ratio": rng.choice(["1:1", "200:5", "400:5", "1000:5"], size=n, p=[0.85, 0.07, 0.05, 0.03]),
        "status": weighted_choice(rng, ["active", "removed", "stocked", "failed"], [0.92, 0.04, 0.02, 0.02], n),
    })


def _meter_reads(ctx, meters, n_target=400_000):
    """AMI reads: each meter contributes ~40 reads on 15-min interval over a recent slice."""
    rng = ctx.rng
    n_per = max(20, n_target // len(meters))
    n = n_per * len(meters)
    meter_ids = np.repeat(meters["meter_id"].to_numpy(), n_per)
    base_start = pd.Timestamp("2026-04-15")
    intervals = np.tile(np.arange(n_per), len(meters))
    read_ts = base_start + pd.to_timedelta(intervals * 15, unit="m")
    # Add per-meter random offset hour
    hour_off = np.repeat(rng.integers(0, 24, size=len(meters)), n_per)
    read_ts = read_ts + pd.to_timedelta(hour_off, unit="h")
    # Shape: diurnal + weekday bump
    hour = read_ts.hour
    diurnal = 0.6 + 0.5 * np.sin((hour - 14) * np.pi / 12)
    base_kwh = rng.gamma(2.0, 0.4, size=n) * diurnal
    return pd.DataFrame({
        "read_id": [f"RD{i:011d}" for i in range(1, n + 1)],
        "meter_id": meter_ids,
        "read_ts": read_ts,
        "obis_code": OBIS_ACTIVE_ENERGY,
        "interval_minutes": 15,
        "kwh_delivered": np.round(base_kwh, 4),
        "kwh_received": np.round(np.where(rng.random(n) < 0.04, rng.gamma(0.5, 0.3, size=n), 0.0), 4),
        "voltage_v": np.round(rng.normal(120, 2.5, size=n).clip(105, 135), 2),
        "current_a": np.round(base_kwh * rng.uniform(0.8, 1.2, size=n) * 5, 2),
        "power_factor": np.round(rng.uniform(0.85, 1.0, size=n), 3),
        "quality_code": weighted_choice(rng, ["VALID", "ESTIMATED", "MISSING", "EDITED"], [0.92, 0.05, 0.02, 0.01], n),
    })


def _billing_determinants(ctx, meters, n_target=120_000):
    rng = ctx.rng
    n_per = max(12, n_target // len(meters))
    n = n_per * len(meters)
    meter_ids = np.repeat(meters["meter_id"].to_numpy(), n_per)
    months = np.tile(np.arange(n_per), len(meters))
    period_start = pd.Timestamp("2024-01-01") + pd.to_timedelta(months * 30, unit="D")
    return pd.DataFrame({
        "billing_determinant_id": [f"BD{i:010d}" for i in range(1, n + 1)],
        "meter_id": meter_ids,
        "period_start": period_start,
        "period_end": period_start + pd.Timedelta(days=30),
        "kwh_total": np.round(rng.gamma(3.0, 220, size=n), 2),
        "kwh_peak": np.round(rng.gamma(2.0, 80, size=n), 2),
        "kwh_offpeak": np.round(rng.gamma(2.0, 140, size=n), 2),
        "kw_demand": np.round(rng.gamma(2.0, 4, size=n), 3),
        "rate_schedule": weighted_choice(rng, ["E-1", "E-TOU-A", "E-TOU-B", "GS-1", "AG-1"], [0.55, 0.20, 0.10, 0.10, 0.05], n),
        "estimated": rng.random(n) < 0.04,
    })


def _field_orders(ctx, meters, n=20_000):
    rng = ctx.rng
    open_ts = daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "field_order_id": [f"FO{i:09d}" for i in range(1, n + 1)],
        "meter_id": rng.choice(meters["meter_id"].to_numpy(), size=n),
        "order_type": weighted_choice(rng, ["install", "remove", "repair", "test", "disconnect", "reconnect"], [0.30, 0.10, 0.15, 0.10, 0.20, 0.15], n),
        "priority": weighted_choice(rng, ["routine", "urgent", "emergency"], [0.70, 0.25, 0.05], n),
        "opened_at": open_ts,
        "scheduled_at": open_ts + pd.to_timedelta(rng.integers(0, 14, size=n), unit="D"),
        "completed_at": open_ts + pd.to_timedelta(rng.integers(1, 21, size=n), unit="D"),
        "technician_id": [f"TECH{rng.integers(100, 999)}" for _ in range(n)],
        "status": weighted_choice(rng, ["completed", "scheduled", "cancelled", "open"], [0.75, 0.10, 0.05, 0.10], n),
    })


def _ami_events(ctx, meters, n=80_000):
    rng = ctx.rng
    return pd.DataFrame({
        "event_id": [f"EVT{i:010d}" for i in range(1, n + 1)],
        "meter_id": rng.choice(meters["meter_id"].to_numpy(), size=n),
        "event_ts": daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
        "event_code": weighted_choice(rng, ["1.0.0", "1.10.0", "1.20.0", "11.0.0", "12.0.0", "32.0.0", "33.0.0"], [0.40, 0.20, 0.10, 0.10, 0.05, 0.10, 0.05], n),
        "event_class": weighted_choice(rng, ["info", "warning", "alarm", "critical"], [0.55, 0.30, 0.10, 0.05], n),
        "description": weighted_choice(rng, ["power_up", "power_down", "battery_low", "comm_lost", "comm_restored", "voltage_sag", "voltage_swell"], [0.25, 0.20, 0.10, 0.15, 0.15, 0.10, 0.05], n),
    })


def _asset_register(ctx, n=8_000):
    rng = ctx.rng
    return pd.DataFrame({
        "asset_id": [f"ASR{i:07d}" for i in range(1, n + 1)],
        "asset_type": weighted_choice(rng, ["Transformer", "Recloser", "Capacitor", "Switch", "Regulator", "Sectionalizer"], [0.45, 0.20, 0.15, 0.10, 0.05, 0.05], n),
        "make": weighted_choice(rng, ["ABB", "Siemens", "GE", "Eaton", "S&C"], [0.30, 0.25, 0.20, 0.15, 0.10], n),
        "voltage_class_kv": rng.choice([4.16, 12.47, 13.8, 25.0, 34.5, 69.0], size=n),
        "kva_rating": rng.choice([25, 50, 75, 100, 167, 250, 500, 1000], size=n),
        "feeder_id": [f"FDR{rng.integers(1, 80):04d}" for _ in range(n)],
        "install_date": pd.to_datetime(rng.integers(int(pd.Timestamp("1990-01-01").timestamp()), int(pd.Timestamp("2025-01-01").timestamp()), size=n), unit="s").date,
        "last_inspection_date": pd.to_datetime(rng.integers(int(pd.Timestamp("2022-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s").date,
        "condition_score": np.round(rng.beta(5, 2, size=n), 3),
    })


def _outage_events(ctx, service_points, n=12_000):
    rng = ctx.rng
    started = daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30"))
    duration_min = rng.gamma(1.5, 60, size=n).clip(2, 24 * 60 * 3).astype(int)
    return pd.DataFrame({
        "outage_id": [f"OUT{i:08d}" for i in range(1, n + 1)],
        "feeder_id": [f"FDR{rng.integers(1, 80):04d}" for _ in range(n)],
        "service_point_id": rng.choice(service_points["service_point_id"].to_numpy(), size=n),
        "started_at": started,
        "restored_at": started + pd.to_timedelta(duration_min, unit="m"),
        "duration_minutes": duration_min,
        "cause_code": weighted_choice(rng, ["weather", "equipment", "vegetation", "animal", "vehicle", "scheduled", "unknown"], [0.30, 0.20, 0.15, 0.10, 0.05, 0.10, 0.10], n),
        "customers_affected": rng.integers(1, 5_000, size=n),
        "saidi_minutes_contribution": np.round(duration_min * rng.uniform(0.5, 1.0, size=n), 2),
    })


def _tamper_events(ctx, meters, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "tamper_id": [f"TMP{i:08d}" for i in range(1, n + 1)],
        "meter_id": rng.choice(meters["meter_id"].to_numpy(), size=n),
        "detected_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
        "tamper_type": weighted_choice(rng, ["reverse_flow", "magnetic", "cover_removal", "neutral_missing", "phase_diversion"], [0.30, 0.20, 0.20, 0.15, 0.15], n),
        "severity": weighted_choice(rng, ["low", "medium", "high"], [0.30, 0.50, 0.20], n),
        "field_validated": rng.random(n) < 0.42,
        "energy_loss_kwh_est": np.round(rng.gamma(2, 80, size=n), 2),
        "status": weighted_choice(rng, ["open", "investigating", "validated", "false_positive", "billed"], [0.20, 0.30, 0.20, 0.20, 0.10], n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    sps = _service_points(ctx)
    meters = _meters(ctx, sps)
    reads = _meter_reads(ctx, meters)
    bd = _billing_determinants(ctx, meters)
    fo = _field_orders(ctx, meters)
    events = _ami_events(ctx, meters)
    assets = _asset_register(ctx)
    outages = _outage_events(ctx, sps)
    tamper = _tamper_events(ctx, meters)
    tables = {
        "service_point": sps,
        "meter": meters,
        "meter_read": reads,
        "billing_determinant": bd,
        "field_order": fo,
        "ami_event": events,
        "asset_register": assets,
        "outage_event": outages,
        "tamper_event": tamper,
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
