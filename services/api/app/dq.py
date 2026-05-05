"""Data Quality module for the Domain Explorer.

Loads rules from data/quality/dq_rules.yaml and executes them against the
populated DuckDB at the repo root. Exposes /dq/run, /dq/summary, /dq/rules,
and /dq/snapshot endpoints.

Each rule's `sql` returns a single integer (failing-row count). Zero == pass.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/dq", tags=["data-quality"])

Severity = Literal["critical", "high", "medium", "low"]


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "quality").is_dir():
            return parent
    raise RuntimeError("Could not locate repo root with data/quality/")


def _rules_path() -> Path:
    return _repo_root() / "data" / "quality" / "dq_rules.yaml"


def _snapshot_path() -> Path:
    return _repo_root() / "data" / "quality" / "last_run.json"


def _duckdb_path() -> Path:
    return _repo_root() / "domain-explorer.duckdb"


class DqRule(BaseModel):
    id: str
    subdomain: str
    table: str
    column: Optional[str] = None
    rule_type: str
    expectation: str
    severity: Severity
    sql: str


class DqResult(BaseModel):
    id: str
    subdomain: str
    table: str
    column: Optional[str]
    rule_type: str
    severity: Severity
    expectation: str
    failing_rows: int
    passed: bool
    duration_ms: int
    error: Optional[str] = None


class DqRunReport(BaseModel):
    ran_at: str
    duckdb_available: bool
    total_rules: int
    passed: int
    failed: int
    errored: int
    pass_rate: float = Field(..., description="passed / executed_rules")
    by_severity: dict[str, dict[str, int]]
    by_subdomain: dict[str, dict[str, int]]
    results: list[DqResult]


@lru_cache(maxsize=1)
def _load_rules() -> list[DqRule]:
    path = _rules_path()
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [DqRule.model_validate(r) for r in raw.get("rules", [])]


def _aggregate(results: list[DqResult]) -> tuple[dict, dict]:
    by_sev: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "errored": 0})
    by_sub: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "errored": 0})
    for r in results:
        bucket = "errored" if r.error else ("passed" if r.passed else "failed")
        by_sev[r.severity][bucket] += 1
        by_sub[r.subdomain][bucket] += 1
    return dict(by_sev), dict(by_sub)


def run_rules() -> DqRunReport:
    """Execute every rule against the local DuckDB and produce a report."""
    rules = _load_rules()
    duckdb_path = _duckdb_path()
    duckdb_available = duckdb_path.exists()

    results: list[DqResult] = []
    if not duckdb_available:
        # Build an "errored" report — useful for surfacing config issues.
        for r in rules:
            results.append(
                DqResult(
                    id=r.id, subdomain=r.subdomain, table=r.table, column=r.column,
                    rule_type=r.rule_type, severity=r.severity, expectation=r.expectation,
                    failing_rows=-1, passed=False, duration_ms=0,
                    error="duckdb file not found",
                )
            )
    else:
        try:
            import duckdb  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"duckdb not available: {exc}")

        con = duckdb.connect(str(duckdb_path), read_only=True)
        try:
            for r in rules:
                start = time.perf_counter()
                err: Optional[str] = None
                failing = -1
                try:
                    row = con.execute(r.sql).fetchone()
                    failing = int(row[0]) if row and row[0] is not None else 0
                except Exception as exc:  # pragma: no cover
                    err = str(exc)[:300]
                duration_ms = int((time.perf_counter() - start) * 1000)
                results.append(
                    DqResult(
                        id=r.id, subdomain=r.subdomain, table=r.table, column=r.column,
                        rule_type=r.rule_type, severity=r.severity, expectation=r.expectation,
                        failing_rows=failing, passed=(err is None and failing == 0),
                        duration_ms=duration_ms, error=err,
                    )
                )
        finally:
            con.close()

    passed = sum(1 for r in results if r.passed)
    errored = sum(1 for r in results if r.error)
    failed = sum(1 for r in results if not r.passed and not r.error)
    executed = passed + failed  # exclude errored from pass-rate denominator
    pass_rate = (passed / executed) if executed else 0.0
    by_sev, by_sub = _aggregate(results)
    return DqRunReport(
        ran_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        duckdb_available=duckdb_available,
        total_rules=len(results),
        passed=passed,
        failed=failed,
        errored=errored,
        pass_rate=round(pass_rate, 4),
        by_severity=by_sev,
        by_subdomain=by_sub,
        results=results,
    )


def write_snapshot(report: DqRunReport) -> Path:
    path = _snapshot_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


@router.get("/rules", response_model=list[DqRule])
def list_rules() -> list[DqRule]:
    return _load_rules()


@router.get("/run", response_model=DqRunReport)
def run() -> DqRunReport:
    return run_rules()


@router.get("/summary")
def summary() -> dict:
    """Lightweight summary suitable for the governance tile."""
    report = run_rules()
    return {
        "ran_at": report.ran_at,
        "duckdb_available": report.duckdb_available,
        "total_rules": report.total_rules,
        "passed": report.passed,
        "failed": report.failed,
        "errored": report.errored,
        "pass_rate": report.pass_rate,
        "by_severity": report.by_severity,
        "by_subdomain": report.by_subdomain,
    }


@router.get("/snapshot")
def snapshot() -> dict:
    path = _snapshot_path()
    if not path.exists():
        raise HTTPException(status_code=404, detail="snapshot not generated yet")
    return json.loads(path.read_text(encoding="utf-8"))
