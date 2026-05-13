"""
Load Pricing & Promotions parquet output into the populated DuckDB.

Mirrors synthetic-data/agentic_commerce/load_to_duckdb.py.

Run:
    python synthetic-data/pricing_and_promotions/load_to_duckdb.py
    python synthetic-data/pricing_and_promotions/load_to_duckdb.py --duckdb /path/to/domain-explorer.duckdb
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

SUBDOMAIN = "pricing_and_promotions"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SYNTH_ROOT = REPO_ROOT / "synthetic-data"
OUT_DIR = SYNTH_ROOT / "output" / SUBDOMAIN
DEFAULT_DUCKDB = REPO_ROOT / "domain-explorer.duckdb"


def load(duckdb_path: Path) -> int:
    if not OUT_DIR.exists():
        raise SystemExit(
            f"FATAL: parquet output dir not found: {OUT_DIR}\n"
            f"       Run synthetic-data/pricing_and_promotions/generate.py first."
        )

    parquets = sorted(OUT_DIR.glob("*.parquet"))
    if not parquets:
        raise SystemExit(
            f"FATAL: no parquet files in {OUT_DIR}\n"
            f"       Run synthetic-data/pricing_and_promotions/generate.py first."
        )

    print(f"Loading {len(parquets)} parquet file(s) from {OUT_DIR}")
    print(f"            into DuckDB at {duckdb_path}")

    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(duckdb_path))
    total = 0
    try:
        con.execute(f'CREATE SCHEMA IF NOT EXISTS "{SUBDOMAIN}"')
        for pq in parquets:
            table = pq.stem
            qualified = f'"{SUBDOMAIN}"."{table}"'
            con.execute(f"DROP TABLE IF EXISTS {qualified}")
            con.execute(
                f"CREATE TABLE {qualified} AS SELECT * FROM read_parquet(?)",
                [str(pq)],
            )
            cnt = con.execute(f"SELECT COUNT(*) FROM {qualified}").fetchone()[0]
            total += cnt
            print(f"  loaded {qualified}: {cnt:,}")
        con.execute("CHECKPOINT")
    finally:
        con.close()

    print(f"done. {total:,} total rows across {len(parquets)} table(s) in schema '{SUBDOMAIN}'.")
    return total


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--duckdb",
        default=os.environ.get("DOMAIN_EXPLORER_DUCKDB", str(DEFAULT_DUCKDB)),
        help="Path to domain-explorer.duckdb (defaults to env DOMAIN_EXPLORER_DUCKDB or repo root).",
    )
    args = p.parse_args()
    load(Path(args.duckdb))


if __name__ == "__main__":
    sys.exit(main())
