@echo off
REM ============================================================================
REM  Domain Explorer — turnkey setup-and-run launcher (Windows)
REM
REM  What this does:
REM    1. Detects Node 22+; if missing, installs a portable copy under node-portable\.
REM    2. Installs pnpm via npm if it's not already available.
REM    3. Runs `pnpm install` at the workspace root.
REM    4. Sets up a Python venv and installs the synthetic-data generators.
REM    5. Generates synthetic data into domain-explorer.duckdb (skipped if it
REM       already exists — first run takes ~5 minutes).
REM    6. Optionally loads everything into Postgres if the user picks that path.
REM    7. Boots `next dev` on port 3030 and opens the browser.
REM
REM  Idempotent — re-run as many times as you like. All output goes to
REM  setup-and-run.log alongside the console.
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"
set "LOG_FILE=%REPO_ROOT%\setup-and-run.log"
set "DUCKDB_FILE=%REPO_ROOT%\domain-explorer.duckdb"
set "VENV_DIR=%REPO_ROOT%\.venv"
set "NODE_PORTABLE_DIR=%REPO_ROOT%\node-portable"
set "NODE_VERSION=v22.11.0"
set "NODE_ZIP_NAME=node-%NODE_VERSION%-win-x64"

REM Stamp the log so multiple runs are easy to tell apart.
echo. >> "%LOG_FILE%" 2>nul
echo ============================================================ >> "%LOG_FILE%" 2>nul
echo [%DATE% %TIME%] setup-and-run.bat starting >> "%LOG_FILE%" 2>nul

call :log "Domain Explorer setup starting from %REPO_ROOT%"

REM --- 1. Node detection -----------------------------------------------------
where node >nul 2>nul
if %ERRORLEVEL%==0 (
    for /f "delims=" %%V in ('node --version') do set "_NODE_V=%%V"
    call :log "Found Node !_NODE_V! on PATH"
) else (
    call :log "Node not found on PATH — installing portable Node %NODE_VERSION% to node-portable\"
    if not exist "%NODE_PORTABLE_DIR%" mkdir "%NODE_PORTABLE_DIR%"
    set "NODE_ZIP_URL=https://nodejs.org/dist/%NODE_VERSION%/%NODE_ZIP_NAME%.zip"
    set "NODE_ZIP_PATH=%NODE_PORTABLE_DIR%\node.zip"

    REM Try curl first (handles SSL revocation issues on locked-down corp boxes),
    REM fall back to PowerShell Invoke-WebRequest.
    where curl >nul 2>nul
    if !ERRORLEVEL!==0 (
        call :log "Downloading Node via curl..."
        curl --ssl-no-revoke -fL -o "!NODE_ZIP_PATH!" "!NODE_ZIP_URL!" >> "%LOG_FILE%" 2>&1
    ) else (
        call :log "Downloading Node via PowerShell..."
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '!NODE_ZIP_URL!' -OutFile '!NODE_ZIP_PATH!'" >> "%LOG_FILE%" 2>&1
    )
    if not exist "!NODE_ZIP_PATH!" (
        call :log "ERROR: failed to download Node zip"
        goto :fail
    )

    call :log "Extracting Node..."
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force -Path '!NODE_ZIP_PATH!' -DestinationPath '%NODE_PORTABLE_DIR%'" >> "%LOG_FILE%" 2>&1
    del "!NODE_ZIP_PATH!" >nul 2>nul

    set "PATH=%NODE_PORTABLE_DIR%\%NODE_ZIP_NAME%;%PATH%"
    call :log "Portable Node installed at %NODE_PORTABLE_DIR%\%NODE_ZIP_NAME%"
)

REM --- 2. pnpm ---------------------------------------------------------------
where pnpm >nul 2>nul
if %ERRORLEVEL%==0 (
    call :log "pnpm already installed"
) else (
    call :log "pnpm not found — installing via npm..."
    call npm install -g pnpm >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: pnpm install via npm failed"
        goto :fail
    )
)

REM --- 3. pnpm install -------------------------------------------------------
call :log "Running pnpm install at workspace root..."
pushd "%REPO_ROOT%"
call pnpm install >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! NEQ 0 (
    call :log "ERROR: pnpm install failed (see %LOG_FILE%)"
    popd
    goto :fail
)
popd

REM --- 4. Backend choice -----------------------------------------------------
echo.
echo ============================================================
echo  Backend selection
echo ============================================================
echo  [D] DuckDB  (default — single file, zero setup)
echo  [P] Postgres (you provide a DATABASE_URL)
echo.
set "BACKEND=duckdb"
set /p "BACKEND_CHOICE=Choose backend [D/p]: "
if /I "%BACKEND_CHOICE%"=="P" set "BACKEND=postgres"
if /I "%BACKEND_CHOICE%"=="postgres" set "BACKEND=postgres"
call :log "Backend selected: %BACKEND%"

set "DATABASE_URL="
if "%BACKEND%"=="postgres" (
    echo.
    set /p "DATABASE_URL=Postgres URL ^(e.g. postgresql://user:pass@localhost:5432/domain_explorer^): "
    if "!DATABASE_URL!"=="" (
        call :log "ERROR: empty Postgres URL"
        goto :fail
    )
)

REM --- 5. Python venv + synthetic data --------------------------------------
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>nul
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: Python 3.11+ is required but not on PATH"
        goto :fail
    )
    set "PY_LAUNCHER=py -3"
) else (
    set "PY_LAUNCHER=python"
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
    call :log "Creating Python venv at %VENV_DIR%..."
    %PY_LAUNCHER% -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: venv creation failed"
        goto :fail
    )
) else (
    call :log "Reusing existing Python venv at %VENV_DIR%"
)

set "VPY=%VENV_DIR%\Scripts\python.exe"
call :log "Upgrading pip / installing synthetic-data deps..."
"%VPY%" -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
"%VPY%" -m pip install duckdb pandas pyarrow faker mimesis numpy pydantic pyyaml >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! NEQ 0 (
    call :log "ERROR: pip install of base deps failed"
    goto :fail
)
if "%BACKEND%"=="postgres" (
    call :log "Installing Postgres driver..."
    "%VPY%" -m pip install "psycopg[binary]" sqlalchemy >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: psycopg install failed"
        goto :fail
    )
)

REM Generate (or reuse) synthetic data.
if exist "%DUCKDB_FILE%" (
    call :log "Synthetic data already present at %DUCKDB_FILE% — skipping generation"
) else (
    call :log "Generating synthetic data ^(first run, ~5 minutes^)..."
    "%VPY%" "%REPO_ROOT%\synthetic-data\generate_all.py" --seed 42 >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: synthetic data generation failed"
        goto :fail
    )
    call :log "Synthetic data generation complete"
)

if "%BACKEND%"=="postgres" (
    call :log "Loading data into Postgres at %DATABASE_URL%..."
    "%VPY%" "%REPO_ROOT%\synthetic-data\load_to_postgres.py" --postgres-url "%DATABASE_URL%" >> "%LOG_FILE%" 2>&1
    if !ERRORLEVEL! NEQ 0 (
        call :log "ERROR: Postgres load failed"
        goto :fail
    )
)

REM --- 6. Boot Next.js dev server --------------------------------------------
call :log "Starting Next.js dev server on http://localhost:3030 ..."
echo.
echo ============================================================
echo  Booting explorer at http://localhost:3030
echo  Backend: %BACKEND%
echo  Press Ctrl+C in this window to stop the server.
echo ============================================================
echo.

start "" http://localhost:3030

set "DB_BACKEND=%BACKEND%"
pushd "%REPO_ROOT%\apps\explorer-web"
call pnpm exec next dev -p 3030
popd
goto :eof

:log
echo [setup-and-run] %~1
echo [%DATE% %TIME%] %~1 >> "%LOG_FILE%" 2>nul
goto :eof

:fail
echo.
echo Setup failed. See %LOG_FILE% for the full transcript.
echo.
exit /b 1
