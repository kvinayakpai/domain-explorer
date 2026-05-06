#!/usr/bin/env bash
# ============================================================================
# Domain Explorer — turnkey setup-and-run launcher (macOS / Linux)
#
# What this does:
#   1. Detects Node 22+; if missing, installs a portable copy under node-portable/.
#   2. Installs pnpm via npm if not present.
#   3. Runs `pnpm install` at the workspace root.
#   4. Sets up a Python venv, installs synthetic-data deps.
#   5. Generates synthetic data into domain-explorer.duckdb (skipped if it
#      already exists — first run takes ~5 minutes).
#   6. Optionally loads everything into Postgres if the user picks that path.
#   7. Boots `next dev` on port 3030 and opens the browser.
#
# Idempotent — safe to re-run. All output is mirrored to setup-and-run.log.
# ============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$REPO_ROOT/setup-and-run.log"
DUCKDB_FILE="$REPO_ROOT/domain-explorer.duckdb"
VENV_DIR="$REPO_ROOT/.venv"
NODE_PORTABLE_DIR="$REPO_ROOT/node-portable"
NODE_VERSION="v22.11.0"

log() {
    local msg="$*"
    echo "[setup-and-run] $msg"
    printf '[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$msg" >> "$LOG_FILE" 2>/dev/null || true
}

fail() {
    log "ERROR: $*"
    log "See $LOG_FILE for the full transcript."
    exit 1
}

{
    echo
    echo "============================================================"
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] setup-and-run.sh starting"
} >> "$LOG_FILE" 2>/dev/null || true

log "Domain Explorer setup starting from $REPO_ROOT"

# --- Detect platform for portable Node download -----------------------------
case "$(uname -s)" in
    Linux*)  NODE_OS=linux ;;
    Darwin*) NODE_OS=darwin ;;
    *)       NODE_OS=linux ;;
esac
case "$(uname -m)" in
    x86_64|amd64) NODE_ARCH=x64 ;;
    arm64|aarch64) NODE_ARCH=arm64 ;;
    *) NODE_ARCH=x64 ;;
esac
NODE_TAR_NAME="node-${NODE_VERSION}-${NODE_OS}-${NODE_ARCH}"

# --- 1. Node ----------------------------------------------------------------
if command -v node >/dev/null 2>&1; then
    log "Found Node $(node --version) on PATH"
else
    log "Node not found — installing portable Node $NODE_VERSION to node-portable/"
    mkdir -p "$NODE_PORTABLE_DIR"
    NODE_URL="https://nodejs.org/dist/${NODE_VERSION}/${NODE_TAR_NAME}.tar.xz"
    NODE_TAR="$NODE_PORTABLE_DIR/node.tar.xz"
    if command -v curl >/dev/null 2>&1; then
        curl -fL -o "$NODE_TAR" "$NODE_URL" >> "$LOG_FILE" 2>&1 || fail "Node download via curl failed"
    elif command -v wget >/dev/null 2>&1; then
        wget -O "$NODE_TAR" "$NODE_URL" >> "$LOG_FILE" 2>&1 || fail "Node download via wget failed"
    else
        fail "Need curl or wget to download Node"
    fi
    tar -xJf "$NODE_TAR" -C "$NODE_PORTABLE_DIR" >> "$LOG_FILE" 2>&1 || fail "Node extraction failed"
    rm -f "$NODE_TAR"
    export PATH="$NODE_PORTABLE_DIR/$NODE_TAR_NAME/bin:$PATH"
    log "Portable Node ready: $(node --version)"
fi

# --- 2. pnpm ---------------------------------------------------------------
if command -v pnpm >/dev/null 2>&1; then
    log "pnpm already installed: $(pnpm --version)"
else
    log "pnpm not found — installing via npm..."
    npm install -g pnpm >> "$LOG_FILE" 2>&1 || fail "pnpm install via npm failed"
fi

# --- 3. pnpm install -------------------------------------------------------
log "Running pnpm install at workspace root..."
( cd "$REPO_ROOT" && pnpm install ) >> "$LOG_FILE" 2>&1 || fail "pnpm install failed"

# --- 4. Backend choice -----------------------------------------------------
echo
echo "============================================================"
echo " Backend selection"
echo "============================================================"
echo " [D] DuckDB  (default — single file, zero setup)"
echo " [P] Postgres (you provide a DATABASE_URL)"
echo
read -r -p "Choose backend [D/p]: " BACKEND_CHOICE
BACKEND="duckdb"
case "${BACKEND_CHOICE:-D}" in
    p|P|postgres|POSTGRES) BACKEND="postgres" ;;
esac
log "Backend selected: $BACKEND"

DATABASE_URL=""
if [ "$BACKEND" = "postgres" ]; then
    echo
    read -r -p "Postgres URL (e.g. postgresql://user:pass@localhost:5432/domain_explorer): " DATABASE_URL
    [ -n "$DATABASE_URL" ] || fail "empty Postgres URL"
fi

# --- 5. Python venv + synthetic data --------------------------------------
PY_BIN=""
for cand in python3 python; do
    if command -v "$cand" >/dev/null 2>&1; then
        PY_BIN="$cand"
        break
    fi
done
[ -n "$PY_BIN" ] || fail "Python 3.11+ is required but not on PATH"

if [ ! -x "$VENV_DIR/bin/python" ]; then
    log "Creating Python venv at $VENV_DIR..."
    "$PY_BIN" -m venv "$VENV_DIR" >> "$LOG_FILE" 2>&1 || fail "venv creation failed"
else
    log "Reusing existing Python venv at $VENV_DIR"
fi
VPY="$VENV_DIR/bin/python"

log "Upgrading pip / installing synthetic-data deps..."
"$VPY" -m pip install --upgrade pip >> "$LOG_FILE" 2>&1
"$VPY" -m pip install duckdb pandas pyarrow faker mimesis numpy pydantic pyyaml >> "$LOG_FILE" 2>&1 \
    || fail "pip install of base deps failed"

if [ "$BACKEND" = "postgres" ]; then
    log "Installing Postgres driver..."
    "$VPY" -m pip install "psycopg[binary]" sqlalchemy >> "$LOG_FILE" 2>&1 \
        || fail "psycopg install failed"
fi

if [ -f "$DUCKDB_FILE" ]; then
    log "Synthetic data already present at $DUCKDB_FILE — skipping generation"
else
    log "Generating synthetic data (first run, ~5 minutes)..."
    "$VPY" "$REPO_ROOT/synthetic-data/generate_all.py" --seed 42 >> "$LOG_FILE" 2>&1 \
        || fail "synthetic data generation failed"
    log "Synthetic data generation complete"
fi

if [ "$BACKEND" = "postgres" ]; then
    log "Loading data into Postgres at $DATABASE_URL..."
    "$VPY" "$REPO_ROOT/synthetic-data/load_to_postgres.py" --postgres-url "$DATABASE_URL" \
        >> "$LOG_FILE" 2>&1 || fail "Postgres load failed"
fi

# --- 6. Boot Next.js dev server --------------------------------------------
log "Starting Next.js dev server on http://localhost:3030 ..."
echo
echo "============================================================"
echo " Booting explorer at http://localhost:3030"
echo " Backend: $BACKEND"
echo " Press Ctrl+C to stop."
echo "============================================================"
echo

# Open the browser in the background — best-effort.
( sleep 3 && {
    if command -v open >/dev/null 2>&1; then
        open http://localhost:3030 || true
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3030 || true
    fi
} ) &

export DB_BACKEND="$BACKEND"
[ -n "$DATABASE_URL" ] && export DATABASE_URL

cd "$REPO_ROOT/apps/explorer-web"
exec pnpm exec next dev -p 3030
