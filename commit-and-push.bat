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

set "COMMIT_MSG=feat: LiteLLM-style multi-provider abstraction for assistant + response cache + canned-answer fallback"

pushd "%REPO_ROOT%"

git add -A
if errorlevel 1 goto :try_alt_index

git commit -m "%COMMIT_MSG%" -m "apps/explorer-web/lib/llm/: new vendor-agnostic chat abstraction with a single public entry chat({system,messages,persona,signal}) returning an async iterable of LLMChunk events (content / citation / done). types.ts defines the shared interface, provider.ts has a RefStreamBuffer that extracts [REF:<id>] markers across deltas, and there are five concrete providers: provider-anthropic.ts (existing @anthropic-ai/sdk), provider-openai.ts, provider-google.ts (@google/generative-ai), provider-litellm.ts (POSTs to LITELLM_BASE_URL with an OpenAI-compatible /v1/chat/completions payload), and provider-mock.ts (deterministic, always-on safety net used in tests and the offline demo)." -m "apps/explorer-web/lib/llm/failover.ts: meta-provider that tries each provider in order, falls through on rate-limit/timeout/5xx, and tracks last-success so subsequent calls start from the known-good one. Auth-class errors propagate without further retries." -m "apps/explorer-web/lib/llm/cache.ts: in-memory LRU keyed on SHA256({system, messages, persona, model}). Default 200 entries / 1h TTL; replay() yields the recorded chunks with cached:true on the trailing done event so the UI can show a Cached badge. ResponseCache.warm() lets the canned layer pre-seed entries." -m "apps/explorer-web/lib/llm/canned.ts + data/canned-answers.json: 50-entry curated answer set spanning the 16 verticals plus cross-cutting questions (data lineage, data mesh, data product, OpenLineage, knowledge graph, Iceberg vs Delta, 3NF vs Data Vault, STP, etc.). Each entry has a matchSubstring (case-insensitive contains), an optional persona/vertical hint, the response text with [REF:<id>] markers, and a citations[] list. The route handler resolves canned -> cache -> failover[ litellm? -> primary -> secondary -> mock ]." -m "apps/explorer-web/app/api/chat/route.ts: replaces the hard-coded Anthropic SDK invocation with a chat() call from the new library. The system prompt now includes a hard rule that every claim must end with a [REF:<id>] tag; the streaming layer parses these out and emits separate event:citation SSE frames. The route still emits the same event:header / event:delta / event:done envelope, plus event:citation, so the existing client wiring keeps working." -m "apps/explorer-web/components/assistant-chat.tsx: renders citations as inline footnote-style chips with hover previews, and shows a provider badge (Claude / GPT-4 / Gemini / LiteLLM / Cached / Demo Mode) plus an end-to-end latency badge after each answer. Cached responses get an amber badge to make repeat hits visually distinct." -m "apps/explorer-web/__tests__/llm-providers.test.ts: 14 tests covering FailoverProvider (rate-limit fall-through, last-success rerouting, auth propagation), ResponseCache (sub-50ms hit, deterministic key, LRU eviction), canned answers (substring match, >=50 entries loaded, no-match returns null), citation parsing (single-shot extractRefs, cross-delta RefStreamBuffer), provider configuration (LLM_PROVIDERS default, LITELLM_BASE_URL prepend), and an end-to-end chat() routing test that confirms a canned-matching question hits the canned path with citations." -m "apps/explorer-web/next.config.mjs: adds @anthropic-ai/sdk, openai, and @google/generative-ai to serverComponentsExternalPackages and the webpack server externals so the lazy require()s aren't bundled." -m "apps/explorer-web/package.json: adds openai and @google/generative-ai to dependencies. apps/explorer-web/app/assistant/page.tsx: live-mode banner now lists every configured provider in failover order rather than just Claude. .env.example, README.md, NOTES.md: document the new env vars (ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, LITELLM_BASE_URL, LITELLM_API_KEY, LLM_PROVIDERS) and the resolution order." -m "Backwards-compatible: the original Claude-only path still works for users with just ANTHROPIC_API_KEY set (default LLM_PROVIDERS=anthropic,mock). domain-explorer.duckdb and synthetic-data/output/ untouched."

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
