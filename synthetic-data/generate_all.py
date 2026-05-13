"""
Run every subdomain generator at a fixed seed (42), then load all parquet files
into one (or both) of the supported targets:

    --target duckdb     (default) load into ``domain-explorer.duckdb``
    --target postgres            load into a Postgres instance via ``--postgres-url``
    --target both                do both

CSV + Parquet files always land under ``synthetic-data/output/<subdomain>/<table>.{csv,parquet}``,
regardless of target.

Examples
--------

    # DuckDB-only (default — what `setup-and-run` ships with):
    python synthetic-data/generate_all.py --seed 42

    # Postgres only — provide a SQLAlchemy / psycopg-style URL:
    python synthetic-data/generate_all.py --target postgres \\
        --postgres-url postgresql://explorer:explorer@localhost:5432/domain_explorer

    # Skip generation, load existing parquet/csv into Postgres:
    python synthetic-data/generate_all.py --skip-generation --target postgres \\
        --postgres-url postgresql://explorer:explorer@localhost:5432/domain_explorer
"""
from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
import time
from pathlib import Path

# duckdb is intentionally a lazy import inside ``load_into_duckdb`` so that
# Postgres-only deployments (e.g. the portable Postgres bundle) do not need
# to install duckdb at all.

SUBDOMAINS = [
    # Original 7 anchors.
    "payments",
    "p_and_c_claims",
    "merchandising",
    "demand_planning",
    "hotel_revenue_management",
    "mes_quality",
    "pharmacovigilance",
    # 10 new anchors (FHIR / FIX / OMOP / OCPP / OpenRTB / FOCUS / SDTM / IRS MeF / ANSI C12 / ISO 20022).
    "ehr_integrations",
    "capital_markets",
    "smart_metering",
    "clinical_trials",
    "cloud_finops",
    "ev_charging",
    "tax_administration",
    "real_world_evidence",
    "settlement_clearing",
    "programmatic_advertising",
    # 18th deep-tier anchor (AP2 / OpenAI Apps SDK / MCP).
    "agentic_commerce",
    # 12 newest anchors -- retail/CPG/operations.
    "pricing_and_promotions",
    "omnichannel_oms",
    "customer_loyalty_cdp",
    "loss_prevention",
    "returns_reverse_logistics",
    "trade_promotion_management",
    "revenue_growth_management",
    "direct_store_delivery",
    "category_management",
    "sop_supply_chain_planning",
    "predictive_maintenance",
    "procurement_spend_analytics",
]

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNTH_ROOT = Path(__file__).resolve().parent
OUT_ROOT = SYNTH_ROOT / "output"
DUCKDB_PATH = REPO_ROOT / "domain-explorer.duckdb"


def run_generators(seed: int) -> dict[str, dict]:
    results: dict[str, dict] = {}
    sys.path.insert(0, str(SYNTH_ROOT))
    for sub in SUBDOMAINS:
        # Slim bundles (e.g. AC-only) prune subdomain packages from the
        # repo. Skip any whose generator module is absent rather than
        # failing the whole run.
        if not (SYNTH_ROOT / sub).is_dir():
            print(f"[{sub}] not present in this bundle -- skipping.")
            continue
        try:
            module = importlib.import_module(f"{sub}.generate")
        except ModuleNotFoundError:
            print(f"[{sub}] generator module missing -- skipping.")
            continue
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
    import duckdb  # local import — only needed for the duckdb target

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


def load_into_postgres(postgres_url: str) -> None:
    """
    Load every CSV under ``synthetic-data/output/<sub>/`` into Postgres,
    one schema per subdomain. Tables are dropped + recreated each run.

    Requires ``psycopg[binary]``, ``sqlalchemy``, and ``pandas``.
    """
    # Defer imports so DuckDB-only users don't pay the dependency cost.
    try:
        import pandas as pd
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise SystemExit(
            f"Postgres target requires sqlalchemy + psycopg + pandas: {exc}\n"
            "  pip install 'psycopg[binary]' sqlalchemy pandas"
        ) from exc

    # Normalise ``postgresql://`` to the SQLAlchemy psycopg-v3 form.
    sa_url = postgres_url
    if sa_url.startswith("postgres://"):
        sa_url = "postgresql://" + sa_url[len("postgres://") :]
    if sa_url.startswith("postgresql://"):
        sa_url = "postgresql+psycopg://" + sa_url[len("postgresql://") :]

    engine = create_engine(sa_url, future=True)

    with engine.begin() as con:
        for sub in SUBDOMAINS:
            sub_dir = OUT_ROOT / sub
            if not sub_dir.exists():
                continue
            con.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{sub}"'))
            for csv in sorted(sub_dir.glob("*.csv")):
                table = csv.stem
                df = pd.read_csv(csv)
                con.execute(text(f'DROP TABLE IF EXISTS "{sub}"."{table}" CASCADE'))
                df.to_sql(
                    name=table,
                    con=con,
                    schema=sub,
                    if_exists="append",
                    index=False,
                    method="multi",
                    chunksize=2000,
                )
                cnt_row = con.execute(text(f'SELECT COUNT(*) FROM "{sub}"."{table}"')).fetchone()
                cnt = int(cnt_row[0]) if cnt_row else 0
                print(f"  loaded postgres {sub}.{table}: {cnt:,}")

    engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--skip-generation",
        action="store_true",
        help="reuse existing parquet/csv under output/",
    )
    p.add_argument(
        "--target",
        choices=["duckdb", "postgres", "both"],
        default="duckdb",
        help="where to load the generated data",
    )
    p.add_argument(
        "--postgres-url",
        default=os.environ.get("DATABASE_URL"),
        help="Postgres URL (required for --target postgres|both); "
             "defaults to env DATABASE_URL",
    )
    args = p.parse_args()

    if args.target in {"postgres", "both"} and not args.postgres_url:
        raise SystemExit(
            "--postgres-url is required when --target is 'postgres' or 'both' "
            "(or set the DATABASE_URL env var)"
        )

    if not args.skip_generation:
        run_generators(args.seed)

    if args.target in {"duckdb", "both"}:
        print(f"Loading into DuckDB at {DUCKDB_PATH}")
        load_into_duckdb()

    if args.target in {"postgres", "both"}:
        print(f"Loading into Postgres at {args.postgres_url}")
        load_into_postgres(args.postgres_url)

    print("done.")


if __name__ == "__main__":
    main()
