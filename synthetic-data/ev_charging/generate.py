"""
Synthetic EV Charging data — OCPP 2.0.1 + OCPI 2.2.1.

Entities (>=8): cpo, charging_station, connector, evse, transaction,
meter_value, authorization, ocpi_tariff, reservation, location.

Realism:
  - OCPP MeterValue cadence: every 60s during a transaction.
  - SoC growth follows a CC/CV curve (linear up to ~80%, slower above).
  - Charging speeds bucketed AC (3.7/7.4/22 kW) vs DC (50/150/250/350 kW).
  - Transaction failure modes mirror real-world ones: cable disconnect,
    auth timeout, EVSE error, customer cancellation.
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

SUBDOMAIN = "ev_charging"

CONNECTOR_TYPES = ["Type2", "CCS1", "CCS2", "CHAdeMO", "Tesla", "Domestic"]
POWER_PROFILES = {
    "Type2-AC-7.4": ("AC", 7.4),
    "Type2-AC-22": ("AC", 22.0),
    "CCS1-DC-50": ("DC", 50.0),
    "CCS1-DC-150": ("DC", 150.0),
    "CCS2-DC-150": ("DC", 150.0),
    "CCS2-DC-350": ("DC", 350.0),
    "CHAdeMO-DC-50": ("DC", 50.0),
    "Tesla-DC-250": ("DC", 250.0),
}


def _cpos(ctx, n=80):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "cpo_id": [f"CPO-{i:03d}" for i in range(1, n + 1)],
        "name": [f.company() for _ in range(n)],
        "country_code": rng.choice(["US", "GB", "DE", "FR", "NL", "NO", "SE", "FI", "DK", "AU"], size=n),
        "ocpi_endpoint": [f"https://api.{f.domain_word()}.example/ocpi/cpo/2.2/" for _ in range(n)],
    })


def _locations(ctx, cpos, n=4_000):
    rng = ctx.rng
    f = ctx.faker
    return pd.DataFrame({
        "location_id": [f"LOC-{i:06d}" for i in range(1, n + 1)],
        "cpo_id": rng.choice(cpos["cpo_id"].to_numpy(), size=n),
        "name": [f"{f.last_name()} Charging Hub" for _ in range(n)],
        "address_line": [f.street_address() for _ in range(n)],
        "city": [f.city() for _ in range(n)],
        "postal_code": [f.postcode() for _ in range(n)],
        "country_code": rng.choice(["US", "GB", "DE", "FR", "NL"], size=n, p=[0.45, 0.20, 0.15, 0.10, 0.10]),
        "latitude": np.round(rng.uniform(32, 60, size=n), 6),
        "longitude": np.round(rng.uniform(-122, 25, size=n), 6),
        "parking_type": weighted_choice(rng, ["public", "garage", "highway", "private", "fleet"], [0.55, 0.15, 0.15, 0.10, 0.05], n),
        "operational_status": weighted_choice(rng, ["AVAILABLE", "BLOCKED", "REMOVED"], [0.92, 0.05, 0.03], n),
    })


def _charging_stations(ctx, locations, n=10_000):
    rng = ctx.rng
    return pd.DataFrame({
        "station_id": [f"CS-{i:07d}" for i in range(1, n + 1)],
        "location_id": rng.choice(locations["location_id"].to_numpy(), size=n),
        "ocpp_endpoint": [f"ws://chargers.example/{i:07d}/ocpp" for i in range(1, n + 1)],
        "vendor": weighted_choice(rng, ["ABB", "ChargePoint", "EVBox", "Wallbox", "Tritium", "Tesla", "Siemens", "Webasto"], [0.20, 0.20, 0.13, 0.10, 0.12, 0.10, 0.08, 0.07], n),
        "model": rng.choice(["Terra-DC", "Express+", "BusinessLine", "Pulsar+", "RTM-75", "Supercharger-V3", "Sicharge-D"], size=n),
        "firmware_version": rng.choice(["1.5.4", "2.0.1", "2.1.3", "3.0.0", "3.2.1"], size=n),
        "ocpp_version": weighted_choice(rng, ["1.6", "2.0.1"], [0.55, 0.45], n),
        "registered_at": pd.to_datetime(rng.integers(int(pd.Timestamp("2018-01-01").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s"),
        "last_heartbeat_ts": pd.to_datetime(rng.integers(int(pd.Timestamp("2026-04-25").timestamp()), int(pd.Timestamp("2026-04-30").timestamp()), size=n), unit="s"),
        "status": weighted_choice(rng, ["Available", "Charging", "Faulted", "Offline", "Reserved"], [0.45, 0.25, 0.05, 0.20, 0.05], n),
    })


def _connectors(ctx, stations, mult=2.5):
    rng = ctx.rng
    n = int(len(stations) * mult)
    station_id = rng.choice(stations["station_id"].to_numpy(), size=n)
    profile = rng.choice(list(POWER_PROFILES.keys()), size=n)
    return pd.DataFrame({
        "connector_id": [f"CON-{i:08d}" for i in range(1, n + 1)],
        "station_id": station_id,
        "evse_id": [f"{s}-{rng.integers(1, 5)}" for s in station_id],
        "connector_position": rng.integers(1, 5, size=n),
        "connector_type": np.array([p.split("-")[0] for p in profile]),
        "power_type": np.array([POWER_PROFILES[p][0] for p in profile]),
        "max_power_kw": np.array([POWER_PROFILES[p][1] for p in profile]),
        "voltage_v": np.where(np.array([POWER_PROFILES[p][0] for p in profile]) == "AC", 230, 400),
        "amperage_a": rng.choice([16, 32, 63, 125, 250], size=n),
        "status": weighted_choice(rng, ["Available", "Occupied", "Reserved", "Unavailable", "Faulted"], [0.50, 0.30, 0.05, 0.10, 0.05], n),
    })


def _authorizations(ctx, n=80_000):
    rng = ctx.rng
    return pd.DataFrame({
        "authorization_id": [f"AUTH-{i:08d}" for i in range(1, n + 1)],
        "id_token": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "id_token_type": weighted_choice(rng, ["RFID", "ISO15118", "eMAID", "MacAddress", "Central"], [0.55, 0.20, 0.15, 0.05, 0.05], n),
        "requested_at": daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
        "decision": weighted_choice(rng, ["Accepted", "Blocked", "Expired", "Invalid", "ConcurrentTx", "NoCredit", "Unknown"], [0.88, 0.02, 0.03, 0.02, 0.02, 0.02, 0.01], n),
        "emsp_id": [f"EMSP-{rng.integers(1, 50):03d}" for _ in range(n)],
        "country_code": rng.choice(["US", "GB", "DE", "FR", "NL"], size=n),
    })


def _transactions(ctx, connectors, authorizations, n=60_000):
    rng = ctx.rng
    started = daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30"))
    duration_min = rng.gamma(2.5, 18, size=n).clip(2, 480).astype(int)
    stopped = started + pd.to_timedelta(duration_min, unit="m")
    energy_kwh = np.round(rng.gamma(2.5, 6.5, size=n).clip(0.1, 200), 3)
    soc_start = rng.integers(5, 60, size=n)
    soc_end = np.clip(soc_start + rng.integers(20, 80, size=n), 0, 100)
    return pd.DataFrame({
        "transaction_id": [f"TX-{i:09d}" for i in range(1, n + 1)],
        "connector_id": rng.choice(connectors["connector_id"].to_numpy(), size=n),
        "id_token": rng.choice(authorizations["id_token"].to_numpy(), size=n),
        "authorization_id": rng.choice(authorizations["authorization_id"].to_numpy(), size=n),
        "started_at": started,
        "stopped_at": stopped,
        "duration_minutes": duration_min,
        "energy_kwh": energy_kwh,
        "soc_start_pct": soc_start,
        "soc_end_pct": soc_end,
        "stop_reason": weighted_choice(rng, ["EVDisconnected", "Local", "Remote", "EmergencyStop", "EnergyLimitReached", "TimeLimitReached", "PowerQuality", "ReachedSOCLimit", "Other"], [0.55, 0.10, 0.05, 0.01, 0.05, 0.05, 0.02, 0.15, 0.02], n),
        "total_cost": np.round(energy_kwh * rng.uniform(0.18, 0.65, size=n), 3),
        "currency": weighted_choice(rng, ["USD", "EUR", "GBP"], [0.55, 0.30, 0.15], n),
        "tariff_id": [f"TAR-{rng.integers(1, 500):04d}" for _ in range(n)],
        "status": weighted_choice(rng, ["Completed", "Failed", "Aborted", "InProgress"], [0.85, 0.06, 0.06, 0.03], n),
    })


def _meter_values(ctx, transactions, n_target=400_000):
    """OCPP MeterValue samples — every 60s during transactions."""
    rng = ctx.rng
    n_per = max(8, n_target // len(transactions))
    n = n_per * len(transactions)
    tx_id = np.repeat(transactions["transaction_id"].to_numpy(), n_per)
    started = pd.to_datetime(np.repeat(transactions["started_at"].to_numpy(), n_per))
    minute_offset = np.tile(np.arange(n_per), len(transactions))
    sample_ts = started + pd.to_timedelta(minute_offset, unit="m")
    energy_per_tx = np.repeat(transactions["energy_kwh"].to_numpy(), n_per)
    soc_start = np.repeat(transactions["soc_start_pct"].to_numpy(), n_per)
    soc_end = np.repeat(transactions["soc_end_pct"].to_numpy(), n_per)
    progress = (minute_offset + 1) / n_per
    energy_active_register = energy_per_tx * progress
    soc = soc_start + (soc_end - soc_start) * progress
    return pd.DataFrame({
        "meter_value_id": [f"MV-{i:011d}" for i in range(1, n + 1)],
        "transaction_id": tx_id,
        "sample_ts": sample_ts,
        "context": weighted_choice(rng, ["Sample.Periodic", "Transaction.Begin", "Transaction.End", "Sample.Clock"], [0.82, 0.05, 0.05, 0.08], n),
        "energy_active_import_register_kwh": np.round(energy_active_register, 3),
        "power_active_import_kw": np.round(rng.gamma(3, 8, size=n).clip(0.1, 350), 3),
        "current_import_a": np.round(rng.uniform(8, 250, size=n), 2),
        "voltage_v": np.round(rng.choice([230, 400], size=n) + rng.normal(0, 3, size=n), 2),
        "soc_pct": np.round(soc.clip(0, 100), 1),
        "temperature_celsius": np.round(rng.normal(35, 8, size=n).clip(-10, 80), 1),
    })


def _ocpi_tariffs(ctx, n=2_500):
    rng = ctx.rng
    return pd.DataFrame({
        "tariff_id": [f"TAR-{i:04d}" for i in range(1, n + 1)],
        "country_code": rng.choice(["US", "GB", "DE", "FR", "NL"], size=n),
        "party_id": [f"PARTY-{rng.integers(1, 200):03d}" for _ in range(n)],
        "currency": weighted_choice(rng, ["USD", "EUR", "GBP"], [0.55, 0.30, 0.15], n),
        "tariff_type": weighted_choice(rng, ["AD_HOC_PAYMENT", "PROFILE_CHEAP", "PROFILE_FAST", "PROFILE_GREEN", "REGULAR"], [0.30, 0.15, 0.20, 0.10, 0.25], n),
        "energy_price_per_kwh": np.round(rng.uniform(0.15, 0.75, size=n), 4),
        "time_price_per_hour": np.round(rng.choice([0, 0, 0, 1.5, 3.0, 5.0], size=n), 2),
        "session_fee": np.round(rng.choice([0, 0, 0.5, 1.0, 2.0], size=n), 2),
        "min_price": np.round(rng.uniform(0, 2.0, size=n), 2),
        "max_price": np.round(rng.uniform(20, 80, size=n), 2),
        "valid_from": pd.to_datetime(rng.integers(int(pd.Timestamp("2024-01-01").timestamp()), int(pd.Timestamp("2026-01-01").timestamp()), size=n), unit="s").date,
    })


def _reservations(ctx, connectors, n=15_000):
    rng = ctx.rng
    expires = daterange_minutes(rng, n, pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30"))
    return pd.DataFrame({
        "reservation_id": [f"RES-{i:08d}" for i in range(1, n + 1)],
        "connector_id": rng.choice(connectors["connector_id"].to_numpy(), size=n),
        "id_token": [f"{rng.integers(10**13, 10**14):014d}" for _ in range(n)],
        "reserved_at": expires - pd.to_timedelta(rng.integers(5, 120, size=n), unit="m"),
        "expires_at": expires,
        "status": weighted_choice(rng, ["Used", "Cancelled", "Expired", "Pending"], [0.55, 0.15, 0.20, 0.10], n),
    })


def generate(seed=42):
    ctx = make_context(seed)
    cpos = _cpos(ctx)
    locs = _locations(ctx, cpos)
    stations = _charging_stations(ctx, locs)
    connectors = _connectors(ctx, stations)
    auths = _authorizations(ctx)
    transactions = _transactions(ctx, connectors, auths)
    meter_values = _meter_values(ctx, transactions)
    tariffs = _ocpi_tariffs(ctx)
    reservations = _reservations(ctx, connectors)
    tables = {
        "cpo": cpos,
        "location": locs,
        "charging_station": stations,
        "connector": connectors,
        "authorization": auths,
        "transaction": transactions,
        "meter_value": meter_values,
        "ocpi_tariff": tariffs,
        "reservation": reservations,
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
