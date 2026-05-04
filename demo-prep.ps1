# Domain Explorer demo-prep script
# ------------------------------------------------------------
# Regenerates the synthetic data layer (CSV + parquet + DuckDB)
# that's intentionally NOT committed to git (kept under GitHub's
# recommended size limit). Run this once after cloning, or any
# time you want a fresh deterministic dataset.
#
# Usage (from the repo root):
#   pwsh ./demo-prep.ps1
#
# What it does:
#   1. Verifies Python 3.10+ is available.
#   2. Creates/uses a local .venv at .venv-demo/.
#   3. Installs the synthetic-data package + deps.
#   4. Runs synthetic-data/generate_all.py at seed=42.
#   5. Result: synthetic-data/output/<sub>/ + domain-explorer.duckdb
#      sitting at the repo root, ready for the explorer to read.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "==> Domain Explorer — demo prep" -ForegroundColor Cyan
Write-Host ""

# 1. Check python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $python) {
    Write-Error "Python not found on PATH. Install Python 3.10+ from https://python.org and re-run."
    exit 1
}
$pythonExe = $python.Source
Write-Host "    using $pythonExe" -ForegroundColor Gray

# 2. Create venv
$venv = Join-Path $PSScriptRoot ".venv-demo"
if (-not (Test-Path $venv)) {
    Write-Host "==> Creating virtual env at .venv-demo/" -ForegroundColor Cyan
    & $pythonExe -m venv $venv
}
$venvPython = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    # Linux/macOS layout (in case someone runs via pwsh on a non-Windows host)
    $venvPython = Join-Path $venv "bin/python"
}

# 3. Install deps (synthetic-data is a uv/pip workspace member with its own pyproject)
Write-Host "==> Installing synthetic-data deps" -ForegroundColor Cyan
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -e ./synthetic-data
& $venvPython -m pip install --quiet faker mimesis numpy duckdb pyarrow pandas

# 4. Run generators
Write-Host "==> Generating synthetic data (seed=42, ~4M rows across 7 subdomains)" -ForegroundColor Cyan
Write-Host "    This usually takes 1-3 minutes." -ForegroundColor Gray
& $venvPython ./synthetic-data/generate_all.py --seed 42

# 5. Sanity check
$db = Join-Path $PSScriptRoot "domain-explorer.duckdb"
if (Test-Path $db) {
    $size = [math]::Round((Get-Item $db).Length / 1MB, 1)
    Write-Host ""
    Write-Host "==> Done. domain-explorer.duckdb is $size MB" -ForegroundColor Green
    Write-Host "    Boot the explorer:  pnpm install && pnpm --filter explorer-web dev" -ForegroundColor Gray
} else {
    Write-Error "Expected $db but it wasn't produced. Check synthetic-data/generate_all.py output."
    exit 1
}
