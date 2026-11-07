"""Build the two oil and gas subdomains into a scratch DuckDB and run their dbt models and tests.

Used by CI (and runnable locally): python tools/dbt_oil_gas_check.py
Needs dbt-duckdb on the path; takes a minute or two. No dbt packages are needed, so there is no `dbt deps` step. Exits non-zero on any failure.
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
SYNTH = ROOT / "synthetic-data"
SUBDOMAINS = ["refinery_operations", "upstream_artificial_lift"]


def main() -> int:
    sys.path.insert(0, str(SYNTH))
    work = Path(tempfile.mkdtemp(prefix="dbt-og-"))
    db = work / "og.duckdb"
    con = duckdb.connect(str(db))
    for sub in SUBDOMAINS:
        tables = importlib.import_module(f"{sub}.generate").generate(seed=42)
        con.execute(f'CREATE SCHEMA IF NOT EXISTS "{sub}"')
        for name, df in tables.items():
            con.register("df_in", df)
            con.execute(f'CREATE OR REPLACE TABLE "{sub}"."{name}" AS SELECT * FROM df_in')
            con.unregister("df_in")
        print(f"[{sub}] {len(tables)} tables loaded")
    con.close()

    env = {**os.environ, "DOMAIN_EXPLORER_DUCKDB": str(db)}
    # The full project has pre-existing duplicate model names (two dim_channel), so dbt cannot
    # parse it whole; build a project holding only the two oil and gas model folders.
    src = ROOT / "modeling" / "dbt"
    dbt = work / "dbt"
    dbt.mkdir()
    for f in ("dbt_project.yml", "profiles.yml"):
        shutil.copy(src / f, dbt / f)
    for d in ("macros", "tests"):
        shutil.copytree(src / d, dbt / d)
    for sub in SUBDOMAINS:
        shutil.copytree(src / "models" / sub, dbt / "models" / sub)
    steps = [["dbt", "build", "--select", *SUBDOMAINS, "upstream_artificial_lift_run_life_matches_world"]]
    env["DBT_PROFILES_DIR"] = str(dbt)
    for cmd in steps:
        print("+", " ".join(cmd))
        rc = subprocess.run(cmd, cwd=dbt, env=env).returncode
        if rc:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
