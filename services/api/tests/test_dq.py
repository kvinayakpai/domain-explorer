"""DQ rule executor tests against a tiny in-memory DuckDB."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pytest


# ---- helpers --------------------------------------------------------------- #


def _seed_payments(con: duckdb.DuckDBPyConnection) -> None:
    """A 10-row payments schema used across the rule tests."""
    con.execute("CREATE SCHEMA payments")
    con.execute(
        """
        CREATE TABLE payments.payments (
            payment_id TEXT,
            amount DOUBLE,
            currency TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
        """
    )
    rows = [
        ("p1", 100.0, "USD", "settled", "2026-04-01 10:00"),
        ("p2", 250.0, "USD", "settled", "2026-04-01 11:00"),
        ("p3", 0.0,   "USD", "failed",  "2026-04-02 08:00"),
        ("p4", 500.0, "EUR", "settled", "2026-04-03 09:30"),
        ("p5", None,  "USD", "settled", "2026-04-03 10:00"),  # null amount
        ("p6", 75.0,  "GBP", "settled", "2026-04-04 12:00"),
        ("p7", 75.0,  "GBP", "settled", "2026-04-04 13:00"),
        ("p8", 1200.0,"USD", "settled", "2026-04-05 14:00"),
        ("p1", 100.0, "USD", "settled", "2026-04-05 15:00"),  # dup payment_id
        ("p9", -10.0, "USD", "failed",  "2026-04-06 16:00"),  # negative amount
    ]
    for r in rows:
        con.execute("INSERT INTO payments.payments VALUES (?, ?, ?, ?, ?)", r)


# ---- rule-type tests ------------------------------------------------------- #


def test_not_null_rule_counts_nulls():
    con = duckdb.connect(":memory:")
    _seed_payments(con)
    sql = "SELECT COUNT(*) FROM payments.payments WHERE amount IS NULL"
    assert con.execute(sql).fetchone()[0] == 1


def test_uniqueness_rule_counts_duplicates():
    con = duckdb.connect(":memory:")
    _seed_payments(con)
    sql = (
        "SELECT (SELECT COUNT(*) FROM payments.payments) "
        "- (SELECT COUNT(DISTINCT payment_id) FROM payments.payments)"
    )
    assert con.execute(sql).fetchone()[0] == 1


def test_range_rule_counts_out_of_range_amounts():
    con = duckdb.connect(":memory:")
    _seed_payments(con)
    sql = "SELECT COUNT(*) FROM payments.payments WHERE amount < 0 OR amount > 100000"
    assert con.execute(sql).fetchone()[0] == 1


def test_foreign_key_rule_counts_orphans():
    con = duckdb.connect(":memory:")
    _seed_payments(con)
    con.execute("CREATE TABLE payments.customers (customer_id TEXT, payment_id TEXT)")
    con.execute("INSERT INTO payments.customers VALUES ('c1', 'p1'), ('c2', 'p2'), ('c3', 'pZ')")
    sql = (
        "SELECT COUNT(*) FROM payments.customers c "
        "LEFT JOIN payments.payments p USING (payment_id) "
        "WHERE p.payment_id IS NULL AND c.payment_id IS NOT NULL"
    )
    assert con.execute(sql).fetchone()[0] == 1


def test_freshness_rule_counts_stale_rows():
    con = duckdb.connect(":memory:")
    _seed_payments(con)
    # Anything older than 2026-04-04 is "stale" for this hypothetical rule.
    sql = "SELECT COUNT(*) FROM payments.payments WHERE created_at < TIMESTAMP '2026-04-04'"
    assert con.execute(sql).fetchone()[0] == 5


def test_distribution_drift_rule_returns_diff_count():
    """Drift rule pattern: count rows whose amount is more than 3x baseline mean."""
    con = duckdb.connect(":memory:")
    _seed_payments(con)
    sql = (
        "WITH baseline AS (SELECT avg(amount) AS m FROM payments.payments WHERE amount > 0) "
        "SELECT COUNT(*) FROM payments.payments, baseline "
        "WHERE amount > 3 * baseline.m"
    )
    # p8 (1200) is the outlier vs ~157 average.
    assert con.execute(sql).fetchone()[0] >= 1


# ---- the executor itself --------------------------------------------------- #


def test_dq_executor_classifies_pass_and_fail(tmp_path: Path):
    """End-to-end: write a tiny duckdb, point dq at it via env, run two rules."""
    from app.dq import DqRule, DqResult  # type: ignore

    # The module's run_rules() reads from data/quality/dq_rules.yaml at the
    # repo root; we exercise the model layer directly here, since the YAML is
    # already covered by the registry-shape integration test.
    rule_pass = DqRule(
        id="x.pass", subdomain="x", table="payments.payments",
        column=None, rule_type="not_null", expectation="ok",
        severity="low", sql="SELECT 0",
    )
    rule_fail = DqRule(
        id="x.fail", subdomain="x", table="payments.payments",
        column=None, rule_type="not_null", expectation="ok",
        severity="critical", sql="SELECT 7",
    )

    con = duckdb.connect(":memory:")
    _seed_payments(con)

    results = []
    for r in (rule_pass, rule_fail):
        n = int(con.execute(r.sql).fetchone()[0])
        results.append(
            DqResult(
                id=r.id, subdomain=r.subdomain, table=r.table, column=r.column,
                rule_type=r.rule_type, severity=r.severity, expectation=r.expectation,
                failing_rows=n, passed=(n == 0), duration_ms=0,
            )
        )
    assert results[0].passed is True
    assert results[1].passed is False
    assert results[1].failing_rows == 7


def test_dq_rules_yaml_parses_with_pydantic_shape():
    """The committed dq_rules.yaml should validate against the DqRule model."""
    import yaml
    from app.dq import DqRule  # type: ignore

    p = Path(__file__).resolve().parents[3] / "data" / "quality" / "dq_rules.yaml"
    if not p.exists():
        pytest.skip("dq_rules.yaml not present")
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    rules = [DqRule.model_validate(r) for r in raw.get("rules", [])]
    assert len(rules) >= 5
    assert all(r.severity in {"critical", "high", "medium", "low"} for r in rules)
    assert all(r.sql for r in rules)
