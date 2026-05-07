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

REM Optional: regenerate the master KPI library + per-style SQL stubs from the
REM YAML taxonomy. Comment out if you don't want a fresh sweep on every commit.
REM python tools\build_kpi_master.py

git add -A
if errorlevel 1 goto :try_alt_index

git commit -m "feat: fully attributed data models per subdomain, ERD viewer, enhanced KPI library with per-style SQL" -m "- packages/metadata: extend Zod + Pydantic schemas with entity.attributes[], entity.relationships[], dataModelArtifacts; new KpiMasterEntry + KpiSqlSpec" -m "- data/taxonomy: enrich the 7 anchor subdomains (payments, p_and_c_claims, merchandising, demand_planning, hotel_revenue_management, mes_quality, pharmacovigilance) with full PK/FK/relationship attributes pulled from existing 3NF DDL" -m "- data/kpis/master.yaml: ~210 curated KPIs across all 16 verticals with formula/unit/direction/definition/subdomains[]/related_personas[]" -m "- data/kpis/sql.yaml: 3NF + Vault + Dimensional SQL implementations; real queries for the 7 anchor KPIs against the populated DuckDB; stubs elsewhere" -m "- apps/explorer-web: new components/erd-diagram.tsx (data-driven SVG ERD), /models index + /models/[subdomain]/[style] route, /kpi-library index, extended /kpi/[id] page with per-style SQL viewer and live runner; new POST /api/kpi/[id]/run endpoint" -m "- tools/build_kpi_master.py: generator that aggregates KPIs from data/taxonomy/*.yaml into master.yaml + sql.yaml stubs"
if errorlevel 1 goto :try_alt_index

echo.
echo Commit recorded. Run `git log -1` to confirm the hash, then `git push`
echo when you're ready.
echo.
popd
exit /b 0

:try_alt_index
echo.
echo Standard git failed. Falling back to alternate index in %TEMP%\git-dir-domain-explorer ...
set "GIT_DIR_BACKUP=%GIT_DIR%"
set "GIT_DIR=%TEMP%\git-dir-domain-explorer"
if not exist "%GIT_DIR%" mkdir "%GIT_DIR%"
xcopy /E /I /Y /Q "%REPO_ROOT%\.git\*" "%GIT_DIR%\" >nul 2>&1
git --git-dir="%GIT_DIR%" --work-tree="%REPO_ROOT%" add -A
if errorlevel 1 goto :fail
git --git-dir="%GIT_DIR%" --work-tree="%REPO_ROOT%" commit -m "feat: fully attributed data models per subdomain, ERD viewer, enhanced KPI library with per-style SQL"
if errorlevel 1 goto :fail
echo.
echo Commit recorded against alternate index "%GIT_DIR%". When the workspace
echo settles, replace .git with that directory (rmdir /S /Q .git ^&^& move "%GIT_DIR%" .git)
echo before pushing.
echo.
if defined GIT_DIR_BACKUP (set "GIT_DIR=%GIT_DIR_BACKUP%") else (set "GIT_DIR=")
popd
exit /b 0

:fail
echo.
echo Commit failed. Check the messages above.
echo.
if defined GIT_DIR_BACKUP (set "GIT_DIR=%GIT_DIR_BACKUP%") else (set "GIT_DIR=")
popd
exit /b 1
