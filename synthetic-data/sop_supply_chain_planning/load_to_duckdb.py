"""
Load S&OP / IBP parquet output into the populated DuckDB.

Mirrors the pattern in ``synthetic-data/generate_all.py::load_into_duckdb`` --
``CREATE SCHEMA IF NOT EXISTS`` + ``CREATE TABLE ... AS SELECT * FROM
read_parquet(?)`` for every parquet under
``synthetic-data/output/sop_supply_chain_planning/``.

Unlike ``generate_all.load_into_duckdb`` (which builds a scratch DB then copies
bytes over the repo file), this loader connects directly to the EXISTING
``domain-explorer.duckdb`` so the other anchor schemas stay intact. We only
drop + recreate tables inside the ``sop_supply_chain_planning`` schema.

Run:
    python synthetic-data/sop_supply_chain_planning/load_to_duckdb.py
    python synthetic-data/sop_supply_chain_planning/load_to_duckdb.py --duckdb /path/to/domain-explorer.duckdb

Honours the ``DOMAIN_EXPLORER_DUCKDB`` env var (same one the dbt profile uses)
when ``--duckdb`` is omitted.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import duckdb

SUBDOMAIN = "sop_supply_chain_planning"

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SYNTH_ROOT = REPO_ROOT / "synthetic-data"
OUT_DIR = SYNTH_ROOT / "output" / SUBDOMAIN
DEFAULT_DUCKDB = REPO_ROOT / "domain-explorer.duckdb"


def load(duckdb_path: Path) -> int:
    if not OUT_DIR.exists():
        raise SystemExit(
            f"FATAL: parquet output dir not found: {OUT_DIR}\n"
            f"       Run synthetic-data/sop_supply_chain_planning/generate.py first."
        )

    parquets = sorted(OUT_DIR.glob("*.parquet"))
    if not parquets:
        raise SystemExit(
            f"FATAL: no parquet files in {OUT_DIR}\n"
            f"       Run synthetic-data/sop_supply_chain_planning/generate.py first."
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
