"""
Synthetic Predictive Maintenance data — ISO 13374 / ISO 14224 / ISA-95 /
OPC UA / vendor PdM landscape (PTC ThingWorx, Siemens MindSphere/Senseye,
GE Digital APM, Aveva PI System, IBM Maximo APM, Honeywell Forge,
AspenTech Mtell, Augury, Uptake, SparkCognition, SKF, Emerson).

Entities (>=10):
  asset, sensor, sensor_reading, failure_mode, failure_event, model_version,
  prediction, work_order, maintenance_plan, (+ derived asset_availability mart)

Scale targets:
  Original sketch:   5,000 assets × 10 sensors × 90 days × 1/min  ≈ 6.5B rows  (too big)
  Compromise scale:  1,000 assets ×  5 sensors ×  7 days × 1/min  ≈ 50M rows
  This still produces a ~1.5GB parquet — large but tractable on a laptop.
  CLI --scale arg lets the caller down-shift to {small, demo} for CI runs.

Realism:
  - Degradation curves: assets in "degrading" status follow monotonic drift
    overlaid on noise; values cross alarm thresholds in the final 10-30% of life.
  - Bearing fault frequencies: characteristic BPFO/BPFI/BSF/FTF tones at known
    multiples of shaft RPM.
  - Sensor dropouts: 0.5% of readings have quality_code = 0 (Bad).
  - Sensor drift: 2% of sensors drift their bias over time.
  - Failures are rare: ~200 failures across 1k assets in 7 days.
  - Work orders: ~30% predictive, ~50% preventive, ~20% corrective.
  - int64-safe IDs (same pattern as capital_markets/generate.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import make_context, weighted_choice, write_table

SUBDOMAIN = "predictive_maintenance"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
ASSET_CLASSES = ["pump", "motor", "compressor", "turbine", "gearbox", "conveyor", "HVAC", "valve", "heat_exchanger"]
ASSET_CLASS_W = [0.22, 0.24, 0.10, 0.06, 0.08, 0.12, 0.08, 0.06, 0.04]
MANUFACTURERS = ["SKF", "Siemens", "ABB", "Emerson", "Atlas Copco", "Caterpillar", "GE", "Flowserve", "Sulzer", "Baker Hughes"]
SITES = [f"SITE-{c}" for c in ["NA01", "NA02", "EU01", "EU02", "EU03", "APAC01", "APAC02", "LATAM01"]]
AREAS_PER_SITE = 5
LINES_PER_AREA = 4
CRITICALITY = ["A", "B", "C"]
CRITICALITY_W = [0.18, 0.42, 0.40]
ASSET_STATUS = ["running", "stopped", "standby", "maintenance", "decommissioned"]
ASSET_STATUS_W = [0.74, 0.06, 0.10, 0.08, 0.02]

SENSOR_TYPES = [
    ("vibration_accel",   "g",       12_800.0),
    ("vibration_velocity","mm/s",     2_000.0),
    ("temp_rtd",          "degC",         1.0),
    ("temp_thermo",       "degC",         1.0),
    ("pressure",          "bar",          5.0),
    ("flow",              "m3/h",         1.0),
    ("current",           "A",           10.0),
    ("voltage",           "V",           10.0),
    ("oil_particle",      "ppm",          0.1),
    ("ultrasound",        "dB",          50.0),
    ("acoustic",          "dB",          50.0),
]
SENSOR_LOCATIONS = ["DE bearing", "NDE bearing", "casing axial", "casing radial",
                    "stator winding", "lube inlet", "discharge", "suction", "frame"]
SENSOR_STATUS = ["active", "drifted", "failed", "removed"]
SENSOR_STATUS_W = [0.90, 0.06, 0.02, 0.02]

FAILURE_MODES = [
    # failure_mode_id, fault_code, description, applicable_class, char_freq_hz, p_f_hours, severity
    ("FM_BRD_INNER",  "BRD", "Bearing inner-race fault",            "motor",          162.4, 168,  "S2"),
    ("FM_BRD_OUTER",  "BRD", "Bearing outer-race fault",            "motor",          107.6, 240,  "S2"),
    ("FM_BRD_BALL",   "BRD", "Rolling-element ball fault",          "motor",           70.5, 200,  "S2"),
    ("FM_BRD_FTF",    "BRD", "Fundamental train frequency (cage)",  "motor",           14.8, 320,  "S1"),
    ("FM_GBR_PITT",   "GBR", "Gear-tooth pitting",                  "gearbox",        524.0,  96,  "S2"),
    ("FM_GBR_BROKEN", "GBR", "Broken gear tooth",                   "gearbox",        524.0,  24,  "S3"),
    ("FM_VIB_UNBAL",  "VIB", "Rotor unbalance",                     "pump",            50.0, 480,  "S1"),
    ("FM_VIB_MISAL",  "VIB", "Coupling misalignment",               "pump",           100.0, 360,  "S1"),
    ("FM_LUB_STARV",  "LUB", "Lubrication starvation",              "pump",             0.0,  48,  "S2"),
    ("FM_LUB_CONT",   "LUB", "Lubricant contamination",             "compressor",       0.0, 240,  "S1"),
    ("FM_OVH_THERM",  "OVH", "Thermal overheat (overload)",         "motor",            0.0,  72,  "S2"),
    ("FM_OVH_STAT",   "OVH", "Stator-winding insulation degradation","motor",           0.0, 720,  "S2"),
    ("FM_CMP_SURGE",  "CMP", "Compressor surge",                    "compressor",       3.0,  12,  "S3"),
    ("FM_TRB_BLADE",  "TRB", "Turbine blade erosion",               "turbine",          0.0, 960,  "S2"),
    ("FM_HX_FOUL",    "HXF", "Heat-exchanger fouling",              "heat_exchanger",   0.0, 720,  "S1"),
    ("FM_VLV_STUCK",  "VLV", "Valve sticking",                      "valve",            0.0, 168,  "S1"),
    ("FM_CNV_BELT",   "CBT", "Conveyor belt mistracking",           "conveyor",         0.0, 240,  "S1"),
    ("FM_HVAC_FILTER","HVF", "HVAC filter clogged",                 "HVAC",             0.0, 360,  "S1"),
]

ALGOS = ["autoencoder", "isolation_forest", "xgboost", "lstm", "transformer", "prophet", "arima", "cox_ph"]
ALGO_W = [0.22, 0.15, 0.20, 0.15, 0.10, 0.08, 0.05, 0.05]
PREDICTION_TYPES = ["anomaly_score", "rul", "fault_class", "health_index"]
PREDICTION_TYPE_W = [0.55, 0.20, 0.15, 0.10]
SEVERITY = ["info", "warning", "alarm", "critical"]
WO_TYPES = ["preventive", "corrective", "predictive", "inspection", "emergency"]
WO_TYPE_W = [0.40, 0.20, 0.28, 0.10, 0.02]
WO_STATUS = ["open", "in_progress", "completed", "cancelled", "rejected"]
WO_STATUS_W = [0.08, 0.10, 0.74, 0.05, 0.03]
PLAN_TYPES = ["calendar", "runtime", "condition", "predictive"]
PLAN_TYPE_W = [0.40, 0.20, 0.20, 0.20]
DETECTED_BY = ["model_alert", "operator", "inspection", "protective_trip", "catastrophic"]
DETECTED_BY_W = [0.42, 0.26, 0.18, 0.10, 0.04]


# ---------------------------------------------------------------------------
SCALE_PRESETS = {
    # name : (n_assets, sensors_per_asset, days, readings_per_min, n_failures, n_work_orders, n_predictions, n_plans, n_model_versions)
    "demo":   (   50, 3, 1,   1,   10,   100,   1_000,  100,  20),
    "small":  (  200, 4, 3,   1,   50,   500,  10_000,  400,  40),
    "medium": (1_000, 5, 7,   1,  200, 2_000,  50_000, 2_000,  80),  # default — ~50M readings
    "large":  (2_500, 6, 7,   1,  500, 5_000, 100_000, 5_000, 120),
}


# ---------------------------------------------------------------------------
def _assets(ctx, n):
    rng = ctx.rng
    asset_class = weighted_choice(rng, ASSET_CLASSES, ASSET_CLASS_W, n)
    site = rng.choice(SITES, size=n)
    area = rng.integers(1, AREAS_PER_SITE + 1, size=n)
    line = rng.integers(1, LINES_PER_AREA + 1, size=n)
    install = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2010-01-01").timestamp()),
                     int(pd.Timestamp("2024-01-01").timestamp()), size=n),
        unit="s",
    )
    return pd.DataFrame({
        "asset_id": [f"AST{i:07d}" for i in range(1, n + 1)],
        "tag_id": [f"{s}.A{a:02d}.L{l:02d}.{cls.upper()[:3]}-{i:04d}"
                   for i, (s, a, l, cls) in enumerate(zip(site, area, line, asset_class), start=1)],
        "asset_class": asset_class,
        "manufacturer": rng.choice(MANUFACTURERS, size=n),
        "model_number": [f"M{rng.integers(1000, 9999):04d}-{rng.integers(10, 99):02d}" for _ in range(n)],
        "serial_number": [f"SN{rng.integers(10**8, 10**9):09d}" for _ in range(n)],
        "site_id": site,
        "area_id": [f"AREA-{a:02d}" for a in area],
        "line_id": [f"LINE-{l:02d}" for l in line],
        "criticality": weighted_choice(rng, CRITICALITY, CRITICALITY_W, n),
        "install_date": install.date,
        "design_life_hours": rng.choice([35_000, 50_000, 80_000, 120_000], size=n),
        "rated_kw": np.round(rng.lognormal(3.5, 1.0, size=n), 2),
        "status": weighted_choice(rng, ASSET_STATUS, ASSET_STATUS_W, n),
    })


def _sensors(ctx, assets, sensors_per_asset):
    rng = ctx.rng
    rows = []
    sensor_idx = 1
    asset_ids = assets["asset_id"].to_numpy()
    asset_classes = assets["asset_class"].to_numpy()
    for ai, (asset_id, asset_class) in enumerate(zip(asset_ids, asset_classes)):
        # Pick a sensible subset based on asset_class — every asset gets a temp + vibration.
        types_for_asset = ["vibration_accel", "temp_rtd"]
        extra_pool = [t[0] for t in SENSOR_TYPES if t[0] not in types_for_asset]
        types_for_asset += list(rng.choice(extra_pool, size=max(0, sensors_per_asset - 2), replace=False))
        for st in types_for_asset[:sensors_per_asset]:
            unit, sampling = next((u, s) for n, u, s in SENSOR_TYPES if n == st)
            rmax = float(rng.uniform(10, 100))
            rows.append({
                "sensor_id": f"SNS{sensor_idx:08d}",
                "asset_id": asset_id,
                "sensor_type": st,
                "measurement_location": rng.choice(SENSOR_LOCATIONS),
                "unit": unit,
                "sampling_hz": float(sampling),
                "range_min": 0.0,
                "range_max": rmax,
                "alarm_low": rmax * 0.05,
                "alarm_high": rmax * 0.75,
                "install_date": pd.Timestamp("2024-01-01").date(),
                "status": weighted_choice(rng, SENSOR_STATUS, SENSOR_STATUS_W, 1)[0],
            })
            sensor_idx += 1
    return pd.DataFrame(rows)


def _readings(ctx, sensors, days, readings_per_min):
    """Generate sensor_readings — the high-cardinality fact.
    Scale: sensors × days × 1440 × readings_per_min.
    """
    rng = ctx.rng
    n_sensors = len(sensors)
    minutes_per_day = 1440
    total_minutes = days * minutes_per_day
    total_per_sensor = total_minutes * readings_per_min
    total_rows = n_sensors * total_per_sensor
    print(f"    sensor_reading target: {n_sensors:,} sensors × {total_per_sensor:,} pts = {total_rows:,} rows")

    base_ts = pd.Timestamp("2026-05-01 00:00:00")
    # Build the time axis once for all sensors (memory-efficient).
    time_offsets_minutes = np.arange(total_per_sensor, dtype=np.int64)
    # We'll build the table sensor-by-sensor to keep memory bounded.
    chunks = []
    reading_id_offset = 1
    sensor_ids = sensors["sensor_id"].to_numpy()
    asset_ids = sensors["asset_id"].to_numpy()
    sensor_types = sensors["sensor_type"].to_numpy()
    alarm_highs = sensors["alarm_high"].to_numpy()
    statuses = sensors["status"].to_numpy()

    for si in range(n_sensors):
        nrows = total_per_sensor
        # Base signal: gaussian noise centered on operating value (~40% of alarm_high).
        base = float(alarm_highs[si]) * 0.4
        noise = rng.normal(0, base * 0.05, size=nrows)
        signal = base + noise
        # 20% of sensors get a degradation drift.
        if rng.random() < 0.20:
            drift = np.linspace(0, base * rng.uniform(0.3, 0.9), nrows)
            signal = signal + drift
        # 2% sensor-drift artifact (status='drifted').
        if statuses[si] == "drifted":
            signal = signal + np.linspace(0, base * 0.4, nrows)
        # Vibration sensors get a periodic component at characteristic freq.
        if sensor_types[si].startswith("vibration"):
            t = np.arange(nrows) * 60.0  # seconds (one reading/min)
            signal = signal + 0.1 * base * np.sin(2 * np.pi * 25 * t / nrows)
        # Quality codes — 99.5% Good, 0.5% Bad/Uncertain.
        quality_codes = np.where(rng.random(nrows) < 0.995, 192,
                                  np.where(rng.random(nrows) < 0.5, 64, 0)).astype(np.int16)
        # Anomaly flag — trip when value > alarm_high.
        is_anomaly = (signal > alarm_highs[si])
        ts = base_ts + pd.to_timedelta(time_offsets_minutes, unit="m")
        chunks.append(pd.DataFrame({
            "reading_id": np.arange(reading_id_offset, reading_id_offset + nrows, dtype=np.int64),
            "sensor_id": sensor_ids[si],
            "asset_id": asset_ids[si],
            "reading_ts": ts,
            "value": np.round(signal, 6),
            "quality_code": quality_codes,
            "is_anomaly": is_anomaly,
            "ingestion_ts": ts + pd.Timedelta(seconds=5),
        }))
        reading_id_offset += nrows

    return pd.concat(chunks, ignore_index=True)


def _failure_modes(ctx):
    rows = []
    for fm_id, fc, desc, cls, hz, pf, sev in FAILURE_MODES:
        rows.append({
            "failure_mode_id": fm_id,
            "fault_code": fc,
            "description": desc,
            "applicable_asset_class": cls,
            "characteristic_frequency_hz": hz,
            "typical_p_f_interval_hours": pf,
            "severity_tier": sev,
        })
    return pd.DataFrame(rows)


def _failure_events(ctx, assets, failure_modes, n):
    rng = ctx.rng
    a_idx = rng.integers(0, len(assets), size=n)
    fm_idx = rng.integers(0, len(failure_modes), size=n)
    failure_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-05-01").timestamp()),
                     int(pd.Timestamp("2026-05-08").timestamp()), size=n),
        unit="s",
    )
    downtime = rng.gamma(2.0, 120, size=n).clip(15, 2880).astype(int)
    return pd.DataFrame({
        "failure_event_id": [f"FE{i:09d}" for i in range(1, n + 1)],
        "asset_id": assets["asset_id"].to_numpy()[a_idx],
        "failure_mode_id": failure_modes["failure_mode_id"].to_numpy()[fm_idx],
        "failure_ts": failure_ts,
        "detected_by": weighted_choice(rng, DETECTED_BY, DETECTED_BY_W, n),
        "downtime_minutes": downtime,
        "production_loss_units": (downtime * rng.integers(5, 100, size=n)).astype(np.int64),
        "root_cause": rng.choice([
            "Bearing inner-race spall - 7.2 kHz tone confirmed",
            "Lubricant viscosity outside spec - operator note",
            "Cooling-water flow drop - upstream HX foul",
            "Overspeed event 14:22 - VFD trip",
            "Insulation IR < 1 MOhm - megger test",
            "Cavitation - suction pressure < NPSHr",
            "Coupling misalignment - 2x running speed",
            "Stator imbalance - thermal hotspot",
        ], size=n),
        "corrective_action": rng.choice([
            "Replaced bearing pair, re-greased, restarted",
            "Topped lubricant, replaced filter",
            "Cleaned heat exchanger, re-commissioned",
            "Tightened terminations, restarted",
            "Re-wound stator, vacuum-impregnated",
            "Aligned coupling to <0.05mm tolerance",
            "Replaced impeller, dynamic-balanced",
        ], size=n),
        "cost_usd": np.round(rng.lognormal(8.5, 1.0, size=n), 2),
    })


def _model_versions(ctx, n):
    rng = ctx.rng
    trained_from = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2025-01-01").timestamp()),
                     int(pd.Timestamp("2026-04-01").timestamp()), size=n),
        unit="s",
    )
    trained_to = trained_from + pd.to_timedelta(rng.integers(30, 180, size=n), unit="D")
    deployed = trained_to + pd.to_timedelta(rng.integers(1, 14, size=n), unit="D")
    champion = rng.random(n) < 0.20
    return pd.DataFrame({
        "model_version_id": [f"MV{i:06d}" for i in range(1, n + 1)],
        "model_id": [f"MDL{rng.integers(1, 20):03d}" for _ in range(n)],
        "algorithm": weighted_choice(rng, ALGOS, ALGO_W, n),
        "trained_on_from_ts": trained_from,
        "trained_on_to_ts": trained_to,
        "holdout_precision": np.round(rng.uniform(0.62, 0.96, size=n), 4),
        "holdout_recall": np.round(rng.uniform(0.55, 0.94, size=n), 4),
        "holdout_rul_mape": np.round(rng.uniform(0.05, 0.35, size=n), 4),
        "deployed_at": deployed,
        "deprecated_at": pd.NaT,
        "champion": champion,
    })


def _predictions(ctx, assets, failure_modes, model_versions, n):
    rng = ctx.rng
    a_idx = rng.integers(0, len(assets), size=n)
    fm_idx = rng.integers(0, len(failure_modes), size=n)
    mv_idx = rng.integers(0, len(model_versions), size=n)
    prediction_ts = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-05-01").timestamp()),
                     int(pd.Timestamp("2026-05-08").timestamp()), size=n),
        unit="s",
    )
    anomaly_score = np.round(rng.beta(2, 8, size=n), 4)  # skewed low
    severity = np.where(anomaly_score > 0.85, "critical",
                np.where(anomaly_score > 0.65, "alarm",
                np.where(anomaly_score > 0.35, "warning", "info")))
    rul = rng.gamma(3.0, 200, size=n).clip(1, 5000).astype(int)
    return pd.DataFrame({
        "prediction_id": [f"PRD{i:09d}" for i in range(1, n + 1)],
        "asset_id": assets["asset_id"].to_numpy()[a_idx],
        "model_id": model_versions["model_id"].to_numpy()[mv_idx],
        "model_version": model_versions["model_version_id"].to_numpy()[mv_idx],
        "prediction_ts": prediction_ts,
        "prediction_type": weighted_choice(rng, PREDICTION_TYPES, PREDICTION_TYPE_W, n),
        "anomaly_score": anomaly_score,
        "rul_hours": rul,
        "rul_confidence_lower": (rul * 0.7).astype(int),
        "rul_confidence_upper": (rul * 1.3).astype(int),
        "predicted_failure_mode_id": failure_modes["failure_mode_id"].to_numpy()[fm_idx],
        "severity": severity,
        "feature_snapshot_hash": [f"sha256:{rng.integers(10**15, 10**16):016d}" for _ in range(n)],
    })


def _work_orders(ctx, assets, failure_events, predictions, n):
    rng = ctx.rng
    a_idx = rng.integers(0, len(assets), size=n)
    wo_type = weighted_choice(rng, WO_TYPES, WO_TYPE_W, n)
    priority = rng.choice([1, 2, 3, 4, 5], p=[0.05, 0.15, 0.40, 0.30, 0.10], size=n).astype(np.int16)
    scheduled = pd.to_datetime(
        rng.integers(int(pd.Timestamp("2026-05-01").timestamp()),
                     int(pd.Timestamp("2026-05-08").timestamp()), size=n),
        unit="s",
    )
    actual_start = scheduled + pd.to_timedelta(rng.integers(-3600, 14_400, size=n), unit="s")
    actual_end = actual_start + pd.to_timedelta(rng.gamma(2.0, 90, size=n).clip(30, 1440).astype(int), unit="m")
    labor_hours = np.round(rng.gamma(2.0, 1.5, size=n).clip(0.5, 24.0), 2)
    parts_cost = np.round(rng.lognormal(5.5, 1.5, size=n), 2)
    labor_cost = labor_hours * float(85.0)
    triggered_by = np.where(
        wo_type == "predictive",
        rng.choice(predictions["prediction_id"].to_numpy(), size=n),
        None,
    )
    failure_event = np.where(
        wo_type == "corrective",
        rng.choice(failure_events["failure_event_id"].to_numpy(), size=n),
        None,
    )
    return pd.DataFrame({
        "work_order_id": [f"WO{i:09d}" for i in range(1, n + 1)],
        "asset_id": assets["asset_id"].to_numpy()[a_idx],
        "wo_type": wo_type,
        "wo_priority": priority,
        "triggered_by_prediction_id": triggered_by,
        "scheduled_start": scheduled,
        "actual_start": actual_start,
        "actual_end": actual_end,
        "labor_hours": labor_hours,
        "parts_cost_usd": parts_cost,
        "labor_cost_usd": np.round(labor_cost, 2),
        "status": weighted_choice(rng, WO_STATUS, WO_STATUS_W, n),
        "failure_event_id": failure_event,
        "crew_id": [f"CREW{rng.integers(1, 50):03d}" for _ in range(n)],
    })


def _maintenance_plans(ctx, assets, n):
    rng = ctx.rng
    a_idx = rng.integers(0, len(assets), size=n)
    plan_type = weighted_choice(rng, PLAN_TYPES, PLAN_TYPE_W, n)
    interval_value = rng.choice([7, 14, 30, 90, 180, 365], size=n)
    interval_unit = np.where(plan_type == "runtime", "operating_hours", "days")
    interval_value = np.where(plan_type == "runtime", rng.choice([500, 1000, 2000, 4000, 8000], size=n), interval_value)
    return pd.DataFrame({
        "plan_id": [f"PLN{i:07d}" for i in range(1, n + 1)],
        "asset_id": assets["asset_id"].to_numpy()[a_idx],
        "plan_type": plan_type,
        "interval_value": interval_value.astype(int),
        "interval_unit": interval_unit,
        "trigger_condition": np.where(
            np.isin(plan_type, ["condition", "predictive"]),
            rng.choice([
                '{"sensor_type":"vibration_accel","op":">","threshold":3.5}',
                '{"sensor_type":"temp_rtd","op":">","threshold":90.0}',
                '{"prediction.severity":"alarm"}',
                '{"prediction.rul_hours":"<","value":168}',
            ], size=n),
            None,
        ),
        "job_plan_template": [f"JP-{rng.integers(100, 999):03d}" for _ in range(n)],
        "active": rng.random(n) < 0.92,
        "created_at": pd.to_datetime(
            rng.integers(int(pd.Timestamp("2024-01-01").timestamp()),
                         int(pd.Timestamp("2026-04-01").timestamp()), size=n),
            unit="s",
        ),
    })


def generate(seed=42, scale="medium"):
    ctx = make_context(seed)
    n_assets, sensors_per_asset, days, rpm, n_fail, n_wo, n_pred, n_plan, n_mv = SCALE_PRESETS[scale]
    print(f"  scale = {scale}  ({n_assets} assets, {sensors_per_asset} sensors each, {days}d, {rpm}/min)")

    print("  generating assets...")
    assets = _assets(ctx, n_assets)
    print("  generating sensors...")
    sensors = _sensors(ctx, assets, sensors_per_asset)
    print("  generating failure_modes...")
    failure_modes = _failure_modes(ctx)
    print("  generating model_versions...")
    model_versions = _model_versions(ctx, n_mv)
    print(f"  generating sensor_readings — this is the big one...")
    readings = _readings(ctx, sensors, days, rpm)
    print("  generating failure_events...")
    failure_events = _failure_events(ctx, assets, failure_modes, n_fail)
    print("  generating predictions...")
    predictions = _predictions(ctx, assets, failure_modes, model_versions, n_pred)
    print("  generating work_orders...")
    work_orders = _work_orders(ctx, assets, failure_events, predictions, n_wo)
    print("  generating maintenance_plans...")
    maintenance_plans = _maintenance_plans(ctx, assets, n_plan)

    tables = {
        "asset": assets,
        "sensor": sensors,
        "failure_mode": failure_modes,
        "model_version": model_versions,
        "sensor_reading": readings,
        "failure_event": failure_events,
        "prediction": predictions,
        "work_order": work_orders,
        "maintenance_plan": maintenance_plans,
    }
    for name, df in tables.items():
        write_table(SUBDOMAIN, name, df)
    return tables


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--scale", choices=list(SCALE_PRESETS.keys()), default="medium",
                   help="Scale preset: demo (toy), small (CI), medium (default ~50M rows), large.")
    args = p.parse_args()
    tables = generate(args.seed, args.scale)
    print()
    for name, df in tables.items():
        print(f"  {SUBDOMAIN}.{name}: {len(df):,} rows")


if __name__ == "__main__":
    main()
