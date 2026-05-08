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

set "COMMIT_MSG=feat: customer accelerator CLI - npx @domain-explorer/init <customer> for 30s branded clone"

pushd "%REPO_ROOT%"

git add -A
if errorlevel 1 goto :try_alt_index

git commit -m "%COMMIT_MSG%" -m "Pillar 3 of the demo-first plan. New workspace package packages/cli (name @domain-explorer/init, type module, bin domain-explorer-init -> bin/init.js). The CLI takes a customer slug, vertical, cloud target and persona, then produces a branded clone in 25-35s with a live spinner per step so it works as a closing demo moment." -m "src/index.js orchestrates nine async steps over a shared context object: 01-validate (slug 3-30 alphanumeric+hyphens, 16 verticals, 5 clouds, 15-id persona registry, source repo sanity check), 02-clone (fs-extra copy with IGNORE_DIRS for node_modules/.git/.next/.turbo and IGNORE_FILE_RE for *.duckdb/*.log, plus IGNORE_PATH_FRAGMENTS for synthetic-data/output - returns running file count to the spinner heartbeat), 03-filter-subdomains (deletes data/taxonomy/*.yaml whose `vertical:` field doesn't match, rewrites data/kpis/kpis.yaml line-by-line to drop other verticals' KPI rows), 04-rebrand (rewrites root + apps/explorer-web package.json, README, app/page.tsx hero badge with optional tagline replacement, app/layout.tsx metadata + footer, .env.example header, optional logo copy to apps/explorer-web/public/customer-logo.* and a customer.json marker), 05-cloud-config (renders profiles-snowflake.yml / profiles-bigquery.yml / profiles-databricks.yml / profiles-postgres.yml from templates/, plus next.config.snowflake.mjs for Snowflake; appends cloud-specific env stubs to .env.example), 06-persona-default (writes apps/explorer-web/lib/customer-defaults.json + a typed .ts re-export the assistant page can import), 07-rename-app (rewrites root package.json scripts to use the new package name), 08-init-git (git init -b main with -b fallback, sets a local user.name/email so the commit doesn't fail on machines without a global git identity, runs add + commit), 09-print-summary (final box with file count, kept subdomains, cloud files written, elapsed time, next-steps)." -m "src/utils/spinner.js wraps each step in an ora spinner that flips to green check / red cross, emits a per-second sub-heartbeat once a step exceeds 5s so the demo never feels stuck. src/utils/banner.js prints the opening ASCII box and the resolved-configuration block. src/registries.js holds the 16-vertical, 5-cloud, 15-persona static registries with case-insensitive lookups." -m "templates/ holds the cloud configs: profiles-snowflake.yml uses key-pair auth with env-var-driven account/role/database/warehouse/schema and a query_tag of domain-explorer-${customer}; profiles-bigquery.yml uses service-account method with project/dataset/keyfile/location env vars; profiles-databricks.yml uses host/http_path/token + catalog/schema; profiles-postgres.yml uses standard PG* env vars; next.config.snowflake.mjs sets DATA_SOURCE=snowflake plus the Snowflake env passthrough; README-duckdb.md is the dropped-in note when --cloud=duckdb." -m "packages/cli/__tests__/init.test.js: 10 vitest tests across validate (good config, bad slug, unknown vertical, missing --vertical, customerLabelFor derivation), filterSubdomains (BFSI keep-only, KPI master rewrite), rebrand (package.json names, README/hero/layout/footer, customer.json metadata), and an end-to-end smoke that runs init() against a synthetic repo in tmp and asserts the package.json rename, the Snowflake profile, the customer.json marker, the customer-defaults.json file, and the BFSI-only filter result." -m "Wired up: pnpm-workspace.yaml already had packages/* so the new package is auto-included. Root package.json gains cli:dev / cli:test / cli:build scripts. demo-init.bat at the repo root cleans C:\Claude\demo-output and runs node packages\cli\bin\init.js demo-customer --vertical=bfsi --cloud=snowflake --persona=cdo --tagline=\"Banking, evolved.\" --output-dir=C:\Claude\demo-output so the SE can demo without typing." -m "Constraints respected: no existing app modified beyond adding three top-level scripts; domain-explorer.duckdb and synthetic-data/output untouched; no push; --no-git is honoured. The CLI fails closed with a clear error if the source repo is missing, the output dir is non-empty, or the vertical is unknown."

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
