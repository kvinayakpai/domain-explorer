"""Generate data/quality/last_run.json by running rules against the local DuckDB.

Run from the repo root: `python3 scripts/dq_snapshot.py`.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.dq import run_rules, write_snapshot  # noqa: E402


def main() -> None:
    report = run_rules()
    out = write_snapshot(report)
    pct = round(report.pass_rate * 100, 1)
    print(
        f"wrote {out} — total={report.total_rules} "
        f"passed={report.passed} failed={report.failed} errored={report.errored} "
        f"pass_rate={pct}%"
    )
    if report.failed:
        for r in report.results:
            if not r.passed and not r.error:
                print(f"  FAIL {r.id} ({r.severity}): {r.failing_rows} failing rows — {r.expectation}")


if __name__ == "__main__":
    main()
