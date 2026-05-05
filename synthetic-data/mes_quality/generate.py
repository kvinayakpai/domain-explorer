"""
Synthetic MES / Quality data.

Entities (>=8): plants, lines, work_orders, operations, equipment,
sensor_readings, scrap_events, downtime_events, inspections, defects.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import (
    country_codes,
    daterange_minutes,
    make_context,
    weighted_choice,
    write_table,
)

SUBDOMAIN = "mes_quality"


def _plants(ctx, n=10_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "plant_id": [f"PLT{i:05d}" for i in range(1, n + 1)],
        "plant_name": [f"{f.city()} Plant {i}" for i in range(1, n + 1)],
        "country": rng.choice(country_codes(), size=n),
        "region": weighted_choice(rng, ["NA", "EMEA", "APAC", "LATAM"], [0.35, 0.30, 0.25, 0.10], n),
        "size_sqm": rng.integers(2000, 200_000, size=n),
        "active": rng.random(n) < 0.95,
    })


def _lines(ctx, plants, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "line_id": [f"LN{i:06d}" for i in range(1, n + 1)],
        "plant_id": rng.choice(plants["plant_id"].to_numpy(), size=n),
        "line_type": weighted_choice(rng, ["assembly", "machining", "packaging", "test", "filling"], [0.30, 0.25, 0.20, 0.15, 0.10], n),
        "ideal_cycle_seconds": np.round(rng.uniform(2, 120, size=n), 2),
        "shifts_per_day": rng.choice([1, 2, 3], p=[0.20, 0.40, 0.40], size=n),
    })


def _equipment(ctx, lines, n=15_000):
    rng = ctx.rng
    return pd.DataFrame({
        "equipment_id": [f"EQ{i:07d}" for i in range(1, n + 1)],
        "line_id": rng.choice(lines["line_id"].to_numpy(), size=n),
        "kind": weighted_choice(rng, ["robot_arm", "cnc", "conveyor", "press", "vision_qc", "filler", "wrapper"], [0.20, 0.15, 0.20, 0.15, 0.10, 0.10, 0.10], n),
        "vendor": rng.choice(["Siemens", "ABB", "Fanuc", "KUKA", "Rockwell", "Bosch", "Emerson"], size=n),
        "install_year": rng.integers(2005, 2026, size=n),
        "criticality": weighted_choice(rng, ["A", "B", "C"], [0.20, 0.30, 0.50], n),
    })


def _work_orders(ctx, lines, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "work_order_id": [f"WO{i:08d}" for i in range(1, n + 1)],
        "line_id": rng.choice(lines["line_id"].to_numpy(), size=n),
        "product_code": [f"P{rng.integers(1000, 9999)}" for _ in range(n)],
        "qty_planned": rng.integers(50, 5000, size=n),
        "qty_produced": rng.integers(0, 5000, size=n),
        "started_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
        "ended_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-02"), pd.Timestamp("2026-04-30")),
        "status": weighted_choice(rng, ["completed", "in_progress", "scrapped", "rework"], [0.78, 0.10, 0.05, 0.07], n),
    })


def _operations(ctx, work_orders, n=30_000):
    rng = ctx.rng
    return pd.DataFrame({
        "op_id": [f"OP{i:09d}" for i in range(1, n + 1)],
        "work_order_id": rng.choice(work_orders["work_order_id"].to_numpy(), size=n),
        "step": rng.integers(1, 12, size=n),
        "name": rng.choice(["pick", "place", "weld", "cure", "test", "label", "pack", "ship"], size=n),
        "duration_seconds": np.round(rng.gamma(2.0, 6.0, size=n), 2),
        "operator_id": [f"OPR{rng.integers(1, 5000):05d}" for _ in range(n)],
    })


def _sensor_readings(ctx, equipment, n=300_000):
    rng = ctx.rng
    return pd.DataFrame({
        "reading_id": [f"SR{i:010d}" for i in range(1, n + 1)],
        "equipment_id": rng.choice(equipment["equipment_id"].to_numpy(), size=n),
        "metric": rng.choice(["temperature_c", "vibration_mm_s", "pressure_bar", "torque_nm", "rpm", "current_a"], size=n),
        "value": np.round(rng.normal(50, 8, size=n), 3),
        "ts": daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
        "anomaly": rng.random(n) < 0.02,
    })


def _scrap(ctx, work_orders, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "scrap_id": [f"SCR{i:08d}" for i in range(1, n + 1)],
        "work_order_id": rng.choice(work_orders["work_order_id"].to_numpy(), size=n),
        "qty": rng.integers(1, 200, size=n),
        "reason_code": weighted_choice(rng, ["defective_input", "operator_error", "machine_fault", "wrong_setting", "material"], [0.25, 0.20, 0.30, 0.15, 0.10], n),
        "ts": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
        "cost": np.round(rng.gamma(2.0, 20, size=n), 2),
    })


def _downtime(ctx, equipment, n=10_000):
    rng = ctx.rng
    starts = daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30"))
    durations = rng.gamma(1.5, 25, size=n)
    return pd.DataFrame({
        "downtime_id": [f"DT{i:08d}" for i in range(1, n + 1)],
        "equipment_id": rng.choice(equipment["equipment_id"].to_numpy(), size=n),
        "started_at": starts,
        "ended_at": starts + pd.to_timedelta(durations, unit="m"),
        "category": weighted_choice(rng, ["planned_maintenance", "breakdown", "changeover", "starvation", "blockage", "no_operator"], [0.20, 0.25, 0.20, 0.10, 0.10, 0.15], n),
        "duration_minutes": np.round(durations, 2),
    })


def _inspections(ctx, work_orders, n=20_000):
    rng = ctx.rng
    return pd.DataFrame({
        "inspection_id": [f"INSP{i:08d}" for i in range(1, n + 1)],
        "work_order_id": rng.choice(work_orders["work_order_id"].to_numpy(), size=n),
        "ts": daterange_minutes(rng, n, pd.Timestamp("2024-01-01"), pd.Timestamp("2026-04-30")),
        "result": weighted_choice(rng, ["pass", "fail", "rework"], [0.85, 0.08, 0.07], n),
        "inspector": [f"QC{rng.integers(1,500):04d}" for _ in range(n)],
        "method": weighted_choice(rng, ["visual", "vision_ai", "x_ray", "leak_test", "torque"], [0.35, 0.25, 0.10, 0.15, 0.15], n),
    })


def _defects(ctx, inspections, n_min=10_000):
    rng = ctx.rng
    failed = inspections[inspections["result"].isin(["fail", "rework"])]
    n = max(n_min, len(failed))
    if n > len(failed):
        extras = rng.choice(inspections["inspection_id"].to_numpy(), size=n - len(failed))
        ids = np.concatenate([failed["inspection_id"].to_numpy(), extras])
    else:
        ids = failed["inspection_id"].to_numpy()
    n = len(ids)
    return pd.DataFrame({
        "defect_id": [f"DEF{i:08d}" for i in range(1, n + 1)],
        "inspection_id": ids,
        "code": rng.choice(["D101", "D102", "D201", "D202", "D301", "D401", "D501"], size=n),
        "severity": weighted_choice(rng, ["minor", "major", "critical"], [0.65, 0.30, 0.05], n),
        "category": weighted_choice(rng, ["dimensional", "cosmetic", "functional", "missing_part", "contamination"], [0.30, 0.25, 0.25, 0.10, 0.10], n),
        "logged_at": daterange_minutes(rng, n, pd.Timestamp("2024-01-15"), pd.Timestamp("2026-04-30")),
    })


def generate(seed=42):
    ctx = make_context(seed)
    plants = _plants(ctx)
    lines = _lines(ctx, plants)
    equipment = _equipment(ctx, lines)
    wo = _work_orders(ctx, lines)
    ops = _operations(ctx, wo)
    sensors = _sensor_readings(ctx, equipment)
    scrap = _scrap(ctx, wo)
    downtime = _downtime(ctx, equipment)
    insp = _inspections(ctx, wo)
    defects = _defects(ctx, insp)

    tables = {
        "plants": plants,
        "lines": lines,
        "equipment": equipment,
        "work_orders": wo,
        "operations": ops,
        "sensor_readings": sensors,
        "scrap_events": scrap,
        "downtime_events": downtime,
        "inspections": insp,
        "defects": defects,
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
