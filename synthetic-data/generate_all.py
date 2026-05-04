"""
Run every subdomain generator at a fixed seed (42), then load all parquet files
into a single DuckDB database at the repo root (`domain-explorer.duckdb`),
one schema per subdomain.

CSV + Parquet files land under `synthetic-data/output/<subdomain>/<table>.{csv,parquet}`.

    python synthetic-data/generate_all.py --seed 42
"""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
import time
from pathlib import Path

import duckdb

SUBDOMAINS = [
    "payments",
    "p_and_c_claims",
    "merchandising",
    "demand_planning",
    "hotel_revenue_management",
    "mes_quality",
    "pharmacovigilance",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_ROOT = Path(__file__).resolve().parent
OUT_ROOT = SYNTH_ROOT / "output"
DUCKDB_PATH = REPO_ROOT / "domain-explorer.duckdb"


def run_generators(seed: int) -> dict[str, dict]:
    results: dict[str, dict] = {}
    sys.path.insert(0, str(SYNTH_ROOT))
    for sub in SUBDOMAINS:
        module = importlib.import_module(f"{sub}.generate")
        t0 = time.time()
        tables = module.generate(seed=seed)
        elapsed = time.time() - t0
        results[sub] = {name: len(df) for name, df in tables.items()}
        results[sub]["__elapsed_s__"] = round(elapsed, 1)
        print(f"[{sub}] {sum(len(df) for df in tables.values()):,} rows across {len(tables)} tables in {elapsed:.1f}s")
    return results


def load_into_duckdb() -> None:
    """
    Build the DuckDB at a scratch path then copy bytes over to the repo path.
    On a normal machine you can write directly to DUCKDB_PATH; the scratch
    detour exists because some bind-mount filesystems (Windows virtiofs in
    the CI sandbox) reject unlink even though they accept truncate+write.
    """
    scratch = Path(os.environ.get("TMPDIR", "/tmp")) / "domain-explorer-build.duckdb"
    if scratch.exists():
        scratch.unlink()
    wal = scratch.with_suffix(scratch.suffix + ".wal")
    if wal.exists():
        wal.unlink()

    con = duckdb.connect(str(scratch))
    try:
        for sub in SUBDOMAINS:
            sub_dir = OUT_ROOT / sub
            if not sub_dir.exists():
                continue
            con.execute(f'CREATE SCHEMA IF NOT EXISTS "{sub}"')
            for pq in sorted(sub_dir.glob("*.parquet")):
                table = pq.stem
                qualified = f'"{sub}"."{table}"'
                con.execute(f"DROP TABLE IF EXISTS {qualified}")
                con.execute(
                    f"CREATE TABLE {qualified} AS SELECT * FROM read_parquet(?)",
                    [str(pq)],
                )
                cnt = con.execute(f"SELECT COUNT(*) FROM {qualified}").fetchone()[0]
                print(f"  loaded {qualified}: {cnt:,}")
        con.execute("CHECKPOINT")
    finally:
        con.close()

    print(f"Copying {scratch} -> {DUCKDB_PATH}")
    with open(scratch, "rb") as src, open(DUCKDB_PATH, "wb") as dst:
        shutil.copyfileobj(src, dst)
    target_wal = DUCKDB_PATH.with_suffix(DUCKDB_PATH.suffix + ".wal")
    if target_wal.exists():
        try:
            with open(target_wal, "wb") as f:
                f.truncate(0)
        except OSError:
            pass


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--skip-generation", action="store_true", help="reuse existing parquet under output/")
    args = p.parse_args()
    if not args.skip_generation:
        run_generators(args.seed)
    print(f"Loading into DuckDB at {DUCKDB_PATH}")
    load_into_duckdb()
    print("done.")


if __name__ == "__main__":
    main()
