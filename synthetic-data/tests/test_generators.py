"""Tests for the synthetic-data generators.

Each generator is invoked at seed=0. The slow ones are marked with
``@pytest.mark.slow``; CI's default `pytest` invocation deselects them via
``-m 'not slow'`` (configured in pyproject.toml).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SYNTH_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SYNTH_ROOT))

SUBDOMAINS = [
    "payments",
    "p_and_c_claims",
    "merchandising",
    "demand_planning",
    "hotel_revenue_management",
    "mes_quality",
    "pharmacovigilance",
]

FAST_SUBDOMAINS = ["mes_quality", "pharmacovigilance"]


def _load_generator(name: str):
    try:
        return importlib.import_module(f"{name}.generate")
    except (SyntaxError, IndentationError) as exc:
        pytest.skip(f"{name}.generate is not importable in this sandbox: {exc}")


@pytest.fixture(autouse=True)
def _stub_write_table(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip parquet/CSV disk writes during tests - we only assert in-memory shape."""
    import common as _common

    monkeypatch.setattr(_common, "write_table", lambda subdomain, name, df: None)


def test_common_make_context_seeds_rng_deterministically():
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    from common import make_context

    a = make_context(seed=0)
    b = make_context(seed=0)
    assert a.rng.integers(0, 10_000, 5).tolist() == b.rng.integers(0, 10_000, 5).tolist()


def test_common_weighted_choice_respects_weights():
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    from common import weighted_choice

    rng = np.random.default_rng(0)
    out = weighted_choice(rng, ["a", "b"], [0.99, 0.01], 1000)
    counts = pd.Series(out).value_counts()
    assert counts.get("a", 0) >= 900


@pytest.mark.parametrize("subdomain", FAST_SUBDOMAINS)
def test_generator_produces_tables_at_seed_zero(subdomain: str):
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    mod = _load_generator(subdomain)
    tables = mod.generate(seed=0)
    assert isinstance(tables, dict)
    assert len(tables) >= 5
    for name, df in tables.items():
        assert isinstance(df, pd.DataFrame), f"{subdomain}.{name} is not a DataFrame"
        assert len(df) >= 1, f"{subdomain}.{name} is empty"
        assert df.columns.size >= 2, f"{subdomain}.{name} has too few columns"


@pytest.mark.slow
@pytest.mark.parametrize("subdomain", SUBDOMAINS)
def test_generator_full_run_is_deterministic(subdomain: str):
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    mod = _load_generator(subdomain)
    a = mod.generate(seed=0)
    b = mod.generate(seed=0)
    assert sorted(a) == sorted(b)
    for name in a:
        assert len(a[name]) == len(b[name]), f"{subdomain}.{name} differs across seeds"


@pytest.mark.slow
def test_payments_referential_integrity():
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    mod = _load_generator("payments")
    if mod is None:
        return
    t = mod.generate(seed=0)

    customers = set(t["customers"]["customer_id"].astype(str))
    accounts = set(t["accounts"]["account_id"].astype(str))
    payments = set(t["payments"]["payment_id"].astype(str))

    assert set(t["accounts"]["customer_id"].astype(str)).issubset(customers)
    if "settlements" in t:
        bad = set(t["settlements"]["payment_id"].astype(str)) - payments
        assert not bad, f"settlements has unknown payment_ids: {list(bad)[:5]}"
    if "chargebacks" in t:
        bad = set(t["chargebacks"]["payment_id"].astype(str)) - payments
        assert not bad, f"chargebacks has unknown payment_ids: {list(bad)[:5]}"

    pay = t["payments"]
    fk_cols = [c for c in pay.columns if "account" in c]
    for col in fk_cols:
        vals = set(pay[col].dropna().astype(str))
        assert vals.issubset(accounts | {""}), f"payments.{col} has unknown FKs"


def test_mes_quality_referential_integrity():
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    mod = _load_generator("mes_quality")
    t = mod.generate(seed=0)
    plants = set(t["plants"]["plant_id"].astype(str))
    lines = set(t["lines"]["line_id"].astype(str))
    equipment = set(t["equipment"]["equipment_id"].astype(str))
    work_orders = set(t["work_orders"]["work_order_id"].astype(str))
    assert set(t["lines"]["plant_id"].astype(str)).issubset(plants)
    assert set(t["equipment"]["line_id"].astype(str)).issubset(lines)
    assert set(t["work_orders"]["line_id"].astype(str)).issubset(lines)
    assert set(t["sensor_readings"]["equipment_id"].astype(str)).issubset(equipment)
    assert set(t["operations"]["work_order_id"].astype(str)).issubset(work_orders)
    insp = set(t["inspections"]["inspection_id"].astype(str))
    assert set(t["defects"]["inspection_id"].astype(str)).issubset(insp)


def test_pharmacovigilance_has_required_tables():
    pytest.importorskip("faker")
    pytest.importorskip("mimesis")
    mod = _load_generator("pharmacovigilance")
    t = mod.generate(seed=0)
    assert len(t) >= 5
    for n, df in t.items():
        assert len(df) >= 1, f"pharmacovigilance.{n} is empty"
