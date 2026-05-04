#!/usr/bin/env bash
# Domain Explorer demo-prep script (POSIX)
# Regenerates the synthetic data layer (CSV + parquet + DuckDB)
# that's intentionally NOT committed to git. Run once after clone.
#
# Usage (from the repo root):
#   ./demo-prep.sh

set -euo pipefail
cd "$(dirname "$0")"

echo
echo "==> Domain Explorer — demo prep"
echo

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "ERROR: Python not found on PATH. Install Python 3.10+ and re-run." >&2
  exit 1
fi
echo "    using $PY"

VENV=".venv-demo"
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtual env at $VENV/"
  "$PY" -m venv "$VENV"
fi
VENV_PY="$VENV/bin/python"
if [ ! -x "$VENV_PY" ]; then
  VENV_PY="$VENV/Scripts/python"
fi

echo "==> Installing synthetic-data deps"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -e ./synthetic-data
"$VENV_PY" -m pip install --quiet faker mimesis numpy duckdb pyarrow pandas

echo "==> Generating synthetic data (seed=42, ~4M rows across 7 subdomains)"
echo "    This usually takes 1-3 minutes."
"$VENV_PY" ./synthetic-data/generate_all.py --seed 42

if [ -f domain-explorer.duckdb ]; then
  SIZE_MB=$(du -m domain-explorer.duckdb | cut -f1)
  echo
  echo "==> Done. domain-explorer.duckdb is ${SIZE_MB} MB"
  echo "    Boot the explorer:  pnpm install && pnpm --filter explorer-web dev"
else
  echo "ERROR: Expected domain-explorer.duckdb but it wasn't produced." >&2
  exit 1
fi
