@echo off
REM ============================================================================
REM commit-and-push.bat - host-side commit script
REM
REM Bash was unavailable inside the agent sandbox during this run (workspace
REM was out of inode space, so useradd kept failing). All file edits were
REM authored through the cowork mount; the commit has to be made on the host.
REM Run this script once from the repo root.
REM
REM     commit-and-push.bat
REM
REM This intentionally does NOT push - review the commit, then `git push` when
REM you're happy.
REM ============================================================================

setlocal EnableExtensions

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

set "COMMIT_MSG=feat: lineage diagrams + DQ rules for the 10 new anchors (FHIR, FIX, OMOP, OCPP, OpenRTB, etc.)"

pushd "%REPO_ROOT%"

git add -A
if errorlevel 1 goto :try_alt_index

git commit -m "%COMMIT_MSG%" -m "apps/explorer-web/lib/lineage-data.ts: extends ANCHOR_KEYS, anchorLineages, and anchorSlugs from 7 to 17. Adds 10 new hand-curated LineageGraph entries (ehr_integrations, capital_markets, smart_metering, clinical_trials, cloud_finops, ev_charging, tax_administration, real_world_evidence, settlement_clearing, programmatic_advertising). Each follows the existing 6-column pattern (sources -> staging -> vault hubs/links -> vault sats -> marts -> KPIs) with 30 nodes / ~30 edges, names pulled from each anchor's YAML and DDL." -m "apps/explorer-web/app/lineage/page.tsx + [anchor]/page.tsx: index copy and metadata refreshed from 'seven' to 17 (driven off ANCHOR_KEYS.length). LineageDiagram and LineageThumbnail components are unchanged - they already accept any LineageGraph." -m "data/quality/dq_rules.yaml: appends 41 new DQ rules across the 10 new anchors (4-5 each), spanning not_null / uniqueness / range / foreign_key / freshness / distribution rule types. SQL targets the schemas the synthetic-data generators populate (e.g. ehr_integrations.patient, capital_markets.trade, real_world_evidence.condition_occurrence, tax_administration.\"return\"). The original 31 rules for the 7 anchors are unchanged. Top-of-file TODO marker replaced with a note explaining pending status." -m "data/quality/last_run.json: keeps the existing 7-anchor results AND adds 41 placeholder entries with status='pending - awaiting data generation' and count=null. total_rules bumped to 72; passed/failed/errored unchanged; new top-level pending=41; by_severity and by_subdomain entries get a pending counter. The /dq page handles pending gracefully via small additions in lib/dq.ts (DqResult.status / DqReport.pending), components/dq-rules-table.tsx (Pending status filter + slate Clock pill), and app/dq/page.tsx + app/governance/page.tsx (Pending tile / column)." -m "Synthetic-data generators, DuckDB file, and existing 7 anchors' lineage/DQ are untouched."

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
git --git-dir="%GIT_DIR%" --work-tree="%REPO_ROOT%" commit -m "%COMMIT_MSG%"
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
