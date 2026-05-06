# =============================================================================
# package-zip.ps1 — build the portable Domain Explorer zip
#
# The bundle is *code-only*: it ships the synthetic-data generators (Python),
# the explorer (Next.js), the FastAPI service, the launchers, and the
# documentation. It does NOT include the populated DuckDB or any pre-generated
# CSVs/parquet — those are produced on the target machine on first run by
# setup-and-run.bat / .sh (~5 minutes, deterministic at seed 42).
#
# Usage:
#     powershell -ExecutionPolicy Bypass -File package-zip.ps1
#
# Output:
#     domain-explorer-portable.zip in the repo root
# =============================================================================

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$StagingDir = Join-Path $env:TEMP ("domain-explorer-portable-" + [guid]::NewGuid().ToString("N"))
$OutputZip = Join-Path $RepoRoot "domain-explorer-portable.zip"

Write-Host "[package-zip] Repo root:   $RepoRoot"
Write-Host "[package-zip] Staging dir: $StagingDir"
Write-Host "[package-zip] Output zip:  $OutputZip"

# --- Excludes (regex patterns matched against the relative path) -----------
# ``(?:^|\\)NAME(?:\\|$)`` matches NAME as a path component anywhere in the
# relative path (start, end, or in the middle). PowerShell -match is regex.
$Excludes = @(
    '(?:^|\\)\.git(?:\\|$)',
    '(?:^|\\)node_modules(?:\\|$)',
    '(?:^|\\)\.next(?:\\|$)',
    '(?:^|\\)__pycache__(?:\\|$)',
    '(?:^|\\)\.pytest_cache(?:\\|$)',
    '(?:^|\\)\.ruff_cache(?:\\|$)',
    '(?:^|\\)\.venv(?:\\|$)',
    '(?:^|\\)node-portable(?:\\|$)',
    '(?:^|\\)target(?:\\|$)',
    '(?:^|\\)dist(?:\\|$)',
    '(?:^|\\)build(?:\\|$)',
    '(?:^|\\)out(?:\\|$)',
    '(?:^|\\)\.turbo(?:\\|$)',
    '(?:^|\\)coverage(?:\\|$)',
    '(?:^|\\)synthetic-data\\output(?:\\|$)',
    'pytest-cache-files-',
    '_tmp_',
    '\.tsbuildinfo$',
    '\.pyc$',
    '\.pyo$',
    '\.duckdb$',
    '\.duckdb\.wal$',
    '\.DS_Store$',
    'Thumbs\.db$',
    'desktop\.ini$',
    'setup-and-run\.log$',
    'domain-explorer-portable\.zip$'
)

function ShouldExclude([string]$relPath) {
    foreach ($pattern in $Excludes) {
        if ($relPath -match $pattern) { return $true }
    }
    return $false
}

# --- Stage files -------------------------------------------------------------
New-Item -ItemType Directory -Path $StagingDir -Force | Out-Null
$DestRoot = Join-Path $StagingDir "domain-explorer"
New-Item -ItemType Directory -Path $DestRoot -Force | Out-Null

Write-Host "[package-zip] Copying source files (excluding generated artefacts)..."
$copied = 0
Get-ChildItem -Path $RepoRoot -Recurse -Force -File | ForEach-Object {
    $relPath = $_.FullName.Substring($RepoRoot.Length).TrimStart('\','/')
    if (ShouldExclude $relPath) { return }
    $destPath = Join-Path $DestRoot $relPath
    $destDir = Split-Path -Parent $destPath
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item -LiteralPath $_.FullName -Destination $destPath -Force
    $copied++
}
Write-Host "[package-zip] Copied $copied files."

# --- Ensure synthetic-data/output/ exists as an empty directory -------------
# Nice-to-have: keeps the layout obvious to first-time users.
$emptyOutput = Join-Path $DestRoot "synthetic-data\output"
if (-not (Test-Path $emptyOutput)) {
    New-Item -ItemType Directory -Path $emptyOutput -Force | Out-Null
    Set-Content -Path (Join-Path $emptyOutput ".keep") -Value "Generated CSV/parquet land here on first run.`r`n"
}

# --- Compress to zip ---------------------------------------------------------
if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
Write-Host "[package-zip] Compressing to $OutputZip ..."
Compress-Archive -Path (Join-Path $DestRoot '*') -DestinationPath $OutputZip -CompressionLevel Optimal

# --- Cleanup ----------------------------------------------------------------
Remove-Item -Recurse -Force $StagingDir -ErrorAction SilentlyContinue

$size = (Get-Item $OutputZip).Length
$mb = [math]::Round($size / 1MB, 2)
Write-Host ""
Write-Host "[package-zip] Done. $OutputZip ($mb MB)"
Write-Host "[package-zip] Hand the zip to a user along with this instruction:"
Write-Host "  1. Unzip"
Write-Host "  2. Double-click setup-and-run.bat (Windows) or run ./setup-and-run.sh (mac/linux)"
Write-Host "  3. First run takes ~5 min for data generation; subsequent runs skip that step."
