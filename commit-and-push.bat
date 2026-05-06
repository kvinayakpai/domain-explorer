@echo off
REM ============================================================================
REM commit-and-push.bat — host-side commit script
REM
REM Bash was unavailable inside the agent sandbox during this run, so all the
REM file edits were authored through the cowork mount and the commit has to
REM be made on the host. Run this script once from the repo root.
REM
REM     commit-and-push.bat
REM
REM This intentionally does NOT push — review the commit, then `git push` when
REM you're happy.
REM ============================================================================

setlocal EnableExtensions

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

pushd "%REPO_ROOT%"

git add -A
if errorlevel 1 goto :fail

git commit -m "feat: dual-backend support (DuckDB + Postgres), turnkey setup-and-run launcher" -m "- synthetic-data: --target {duckdb,postgres,both} on generate_all.py + standalone load_to_postgres.py + postgres_schema.sql" -m "- explorer-web: split lib/duckdb.ts into lib/db.ts (backend-agnostic) + lib/db-duckdb.ts + lib/db-postgres.ts; gated by DB_BACKEND env var" -m "- services/api: dq.py runs against either backend with a small dialect translator" -m "- setup-and-run.{bat,sh}: portable Node, pnpm install, Python venv, synthetic-data generation, dev server on port 3030" -m "- package-zip.ps1: build code-only portable bundle (excludes generated DuckDB / CSVs)"
if errorlevel 1 goto :fail

echo.
echo Commit recorded. Run `git log -1` to confirm the hash, then `git push`
echo when you're ready.
echo.

popd
exit /b 0

:fail
echo.
echo Commit failed. Check the messages above.
echo.
popd
exit /b 1
