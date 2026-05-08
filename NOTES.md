# Build & Environment Notes

This document captures the workarounds discovered while building the data
layer and screenshot pipeline. Most of them only matter inside our restricted
sandbox; on a vanilla developer machine the standard commands work as you'd
expect, but the pins below are still good to keep.

## Toolchain

```
Node     22.x   (>=20 also fine)
pnpm     9.x
Python   3.10+  (3.11 recommended; the `from __future__ import annotations` keeps things working on 3.10)
```

Python deps for the synthetic data layer:

```
pip install --break-system-packages faker mimesis numpy pandas pyarrow duckdb
```

## Running the synthetic data pipeline

End to end:

```
python synthetic-data/generate_all.py --seed 42
```

This runs every per-subdomain generator under `synthetic-data/<sub>/generate.py`
at `seed=42`, writes both `*.csv` and `*.parquet` to
`synthetic-data/output/<sub>/`, and loads them into one DuckDB at the repo
root: `domain-explorer.duckdb`, one schema per subdomain (10 tables each, all
≥10 000 rows).

`--skip-generation` reuses the existing parquet output and only re-loads the
DuckDB.

### DuckDB build path detour (sandbox-only)

Some bind-mount filesystems (Windows virtiofs in our CI sandbox) reject
`unlink()` even though they accept truncate-and-rewrite. DuckDB needs to
remove the WAL file at checkpoint time, so building straight onto the mount
fails with `Operation not permitted`. The fix in `generate_all.py` is to
build at `$TMPDIR/domain-explorer-build.duckdb` first, then `shutil.copyfileobj`
the bytes onto the destination path. Skip this detour on a real filesystem.

## Next.js + DuckDB wiring

`apps/explorer-web` reads the populated DuckDB directly via `@duckdb/node-api`
(the prebuilt N-API binding — the older npm `duckdb` package depends on
node-gyp / V8 ABI compatibility and **does not** build on Node 22 in this
sandbox).

Pinned version: `@duckdb/node-api@1.2.0-alpha.15`. The binding it pulls in is
`@duckdb/node-bindings-<platform>-<arch>`; we declare both as
`serverComponentsExternalPackages` and add a webpack `externals` callback in
`apps/explorer-web/next.config.mjs` so the native `.node` file is never
inlined. We also register `node-loader` for any path that does end up
importing a `.node` file directly.

### Trace step + standalone copy

When `output: "standalone"` is used, Next's "Collecting build traces" step
walks the dependency graph but it does not pick up
`@duckdb/node-bindings-linux-x64` (it's a runtime-resolved native dep). After
`pnpm --filter explorer-web build`, copy the binding into the standalone tree:

```
mkdir -p apps/explorer-web/.next/standalone/node_modules/@duckdb
cp -r node_modules/@duckdb/node-bindings-linux-x64 \
      apps/explorer-web/.next/standalone/node_modules/@duckdb/
# (likewise for node-bindings, node-api itself if you want to ship them)
```

then run `node apps/explorer-web/.next/standalone/apps/explorer-web/server.js`.

In the sandbox the trace step itself wouldn't complete (it stalled at
"Collecting build traces"), so for screenshot capture we fell back to plain
`next start` against `.next/server`, which renders identically.

### Other build pins / fixes

- `experimental.typedRoutes` was disabled — the existing scaffolding doesn't
  declare its workspace routes as typed routes, and `typedRoutes: true` causes
  `router.push(string)` and `<Link href={string}>` to fail typechecking in
  several places.
- `lib/duckdb.ts` uses `DuckDBInstance.create(path)` (not `fromFile`) and
  `con.runAndReadAll(sql).getRowObjectsJson()` for serialization safety.

## Multi-provider LLM abstraction

`apps/explorer-web/lib/llm/` exposes a vendor-agnostic `chat({ system,
messages, persona, signal })` entry point used by `app/api/chat/route.ts`.
Concrete providers cover Anthropic (`@anthropic-ai/sdk`), OpenAI (`openai`),
Google Gemini (`@google/generative-ai`), and a LiteLLM proxy (any OpenAI-
compatible endpoint). A `MockProvider` is always available as the final
fallback so demos never break.

Resolution order on every call:

1. **Canned answer** — substring match against
   `data/canned-answers.json` (50 entries spanning the 16 verticals plus
   cross-cutting questions). First hit wins; persona/vertical hints break ties.
2. **Response cache** — in-memory LRU keyed on
   `SHA256({ system, messages, persona, model })`. Default 200 entries / 1 h
   TTL. Cache hits replay the chunk list verbatim with `cached: true` on the
   trailing `done` event so the UI can show a "Cached" badge.
3. **Failover provider chain** — ordered by `LLM_PROVIDERS`
   (default `anthropic,mock`). When `LITELLM_BASE_URL` is set, `litellm` is
   prepended automatically so all traffic flows through the gateway. Rate-
   limit / timeout / 5xx errors fall through to the next provider; the layer
   tracks `last-success` and reorders the chain on subsequent calls.

### Env vars

| Var                  | Purpose                                                             |
| -------------------- | ------------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`  | Claude (default primary)                                            |
| `ANTHROPIC_MODEL`    | Override the Claude model id (default `claude-sonnet-4-6`)          |
| `OPENAI_API_KEY`     | GPT-4 / GPT-4o                                                      |
| `OPENAI_MODEL`       | Override the OpenAI model id (default `gpt-4o-mini`)                |
| `GOOGLE_API_KEY`     | Gemini                                                              |
| `GOOGLE_MODEL`       | Override the Gemini model id (default `gemini-1.5-flash`)           |
| `LITELLM_BASE_URL`   | LiteLLM proxy URL (e.g. `http://localhost:4000`)                    |
| `LITELLM_API_KEY`    | Optional bearer for the proxy                                       |
| `LITELLM_MODEL`      | Override the model id sent to the proxy                             |
| `LLM_PROVIDERS`      | Comma list controlling provider order (default `anthropic,mock`)    |

### Citation discipline

The route handler appends a "EVERY claim must be followed by a `[REF:<id>]`
tag" rule to the system prompt. Each provider streams the model output
through `RefStreamBuffer` which extracts `[REF:<id>]` markers (even when
they're split across delta chunks) and forwards them as separate
`event: citation` SSE frames. The chat UI renders them as inline footnote
chips with hover previews.

## DuckDB API quick reference (1.2.0-alpha)

```ts
const mod = await import("@duckdb/node-api");
const inst = await mod.DuckDBInstance.create("/abs/path/to.duckdb");
const con = await inst.connect();
const reader = await con.runAndReadAll("SELECT 1 as x");
const rows = reader.getRowObjectsJson();   // bigints/decimals as strings
await con.close();
```

`getRowObjectsJson()` is preferred over `getRowObjects()` because Server
Components can't serialize `bigint`s. The `lib/snapshots.ts` helpers coerce
back to numbers as needed.

## Playwright pins (sandbox)

Playwright's default download host (`playwright.azureedge.net`) is blocked in
our sandbox; setting `PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.playwright.dev`
works. Newer Playwright versions reach for newer Chromium builds whose mirror
URL hasn't been published to that CDN yet. The combination that downloads
end-to-end:

```
PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.playwright.dev npm i playwright@1.48
PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.playwright.dev npx playwright install chromium
# resolves to chromium-1140 / Chrome 130.0.6723.31
```

The screenshot script in `screenshots/shoot.js` (mirrored from `/tmp/pw` for
reference; check it in if you want it permanent) launches Chromium with
`--no-sandbox` (bwrap doesn't grant the namespaces Chromium expects),
captures `1280×900` desktop + `390×844 dpr=2` mobile, and writes to
`screenshots/{desktop,mobile}/<route>.png`.

## Reproduction summary

```bash
# 1. Synth data + duckdb
pip install --break-system-packages faker mimesis numpy pandas pyarrow duckdb
python synthetic-data/generate_all.py --seed 42

# 2. Web build
pnpm install
pnpm --filter explorer-web build

# (sandbox-only: copy native bindings into .next/standalone — see above)

# 3. Run + screenshots
node apps/explorer-web/.next/standalone/apps/explorer-web/server.js &
PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.playwright.dev \
  npx -y playwright@1.48 install chromium
node screenshots/shoot.js
```

## Knowledge graph

The KG is built from the YAML registry by `kg/build_graph.py` (NetworkX-backed,
no native deps). It produces:

- `kg/graph.gpickle` — full `MultiDiGraph`, gitignored. Used by the FastAPI
  service for live `/kg/*` queries.
- `kg/graph.json` — committed snapshot with a precomputed force-directed
  layout. The Next.js app loads this directly so the demo runs without the
  API.

```bash
# Regenerate after editing data/.
npm run kg:build
# or, equivalently:
python kg/build_graph.py --data-root data --out kg
```

The assistant grounding layer (`apps/explorer-web/lib/grounding.ts`) prefers
the live API at `$KG_API_URL` if set, falls back to the JSON snapshot, and
falls back again to direct YAML traversal — `bundle.backend` records which
path was taken. See `kg/README.md` for the schema and edge labels.

## Demo flows

`/demo/[vertical]` ships 16 scripted 3-screen tours (one per vertical). Each
maps to a "hero" subdomain — preferring one we have full DDL + DuckDB data
for (Payments, P&C Claims, Merchandising, Demand Planning, Hotel RM,
MES/Quality, Pharmacovigilance), falling back to the highest-leverage
subdomain in the vertical otherwise. The mapping lives in
`apps/explorer-web/lib/demo-flows.ts`.

## Test suites

```bash
# Python — pytest discovers tests under packages/metadata/python/tests,
# services/api/tests, and synthetic-data/tests. Slow generator runs (the
# full 7-subdomain seed=0 suite executed twice per generator) are tagged
# @pytest.mark.slow and deselected in pyproject.toml — opt in via -m slow.
python -m pytest

# TypeScript — vitest, suite under apps/explorer-web/__tests__/.
pnpm --filter explorer-web test
```

CI runs both jobs; see `.github/workflows/ci.yml`.

## Filesystem caveats (sandbox)

The Windows virtiofs bind-mount we use rejects `unlink()` (NOTES has the
DuckDB-specific workaround above; it bites pnpm's store cleanup, file
deletions, and `git`'s `.git/index.lock` cleanup too). Workarounds:

- `pnpm install --store-dir /tmp/pnpm-store` keeps the content-addressable
  store on a writeable tmpfs.
- Stale `.git/index.lock` blocks commits. `cp -r .git /tmp/git-dir-x && rm -f
  /tmp/git-dir-x/index.lock`, run `git --git-dir=/tmp/git-dir-x ...`, then
  copy the modified pieces (`index`, `HEAD`, `refs/heads/*`, `logs/*`,
  `objects/`) back into the real `.git`.
