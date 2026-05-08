# Domain Explorer

A metadata-driven explorer for industry verticals, subdomains, KPIs, source systems, and integration patterns. The whole UI is rendered from a typed registry of YAML configs — add a YAML file, get a page.

## What's in here

```
domain-explorer/
├── apps/explorer-web/      # Next.js 14 App Router UI (TS strict, Tailwind, shadcn/ui)
├── services/api/           # FastAPI service (registry + DQ + KG endpoints)
├── packages/
│   ├── metadata/           # Zod (TS) + Pydantic v2 (Py) schemas, YAML loader
│   └── shared-types/       # generated TS types
├── data/
│   ├── taxonomy/           # subdomain configs (110+ across 16 verticals)
│   ├── glossary/           # business / KPI / regulatory term glossary
│   ├── kpis/               # cross-vertical KPI registry
│   ├── source-systems/     # source system registry
│   ├── connectors/         # connector patterns (23 of them)
│   └── quality/            # DQ rules + last-run snapshot
├── modeling/
│   ├── dbt/                # dbt-core models for Payments (DuckDB)
│   └── ddl/                # 3NF / Vault / dim DDL excerpts (all 7 anchors)
├── kg/
│   ├── build_graph.py      # registry → NetworkX MultiDiGraph + JSON snapshot
│   ├── graph.json          # committed snapshot (loaded by /kg + assistant)
│   ├── cypher/             # openCypher query templates
│   └── ontology/           # OWL/Turtle stubs
├── synthetic-data/         # per-subdomain generators (Faker + numpy)
├── docs/
│   ├── blueprint/          # drop the project blueprint .docx here
│   └── architecture/       # ADRs
└── .github/workflows/      # CI: node + python lint/typecheck/test
```

## Quick start

Prerequisites: Node 20+, pnpm 9+, Python 3.11+ (uv optional).

```bash
# 1. Generate the synthetic data layer (~4M rows, ~90MB DuckDB).
#    This is intentionally NOT in git — kept under GitHub's size limit.
#    Windows / PowerShell:
pwsh ./demo-prep.ps1
#    macOS / Linux:
./demo-prep.sh

# 2. Install JS deps and run the web app
pnpm install
pnpm --filter explorer-web dev

# 3. Build the knowledge graph (also produces kg/graph.json which is committed
#    so the explorer works without any further setup).
npm run kg:build

# 4. (optional) Enable the live multi-provider assistant on /assistant.
cp .env.example .env
# then set ANY ONE of the following provider keys:
#   ANTHROPIC_API_KEY=sk-ant-...        # Claude (default primary)
#   OPENAI_API_KEY=sk-...               # GPT-4 / GPT-4o
#   GOOGLE_API_KEY=...                  # Gemini
#   LITELLM_BASE_URL=http://localhost:4000  # LiteLLM proxy fronting any/all of the above
# Optional: order the providers explicitly (default: anthropic,mock).
#   LLM_PROVIDERS=anthropic,openai,google,mock

# 5. (optional) Run the API
uv run uvicorn app.main:app --reload --app-dir services/api
```

Then open <http://localhost:3000>. The subdomain pages will show live numbers from the regenerated DuckDB.

### Why is the data regenerated and not committed?

The full `domain-explorer.duckdb` is ~91MB and the CSV/parquet sidecars push the total over GitHub's 50MB recommended file size. Since the data is fully deterministic (`--seed 42`), it's cheaper to regenerate on first clone than to host it. The local copy is untouched — you only run `demo-prep` on a fresh clone or to refresh a specific subdomain.

## How the metadata-driven model works

1. YAML files in `data/taxonomy/` define subdomains.
2. `packages/metadata` validates them against Zod (TS) and Pydantic v2 (Python) schemas.
3. The Next.js app reads the typed registry at build/request time and renders the 9-attribute template for every subdomain — no per-page code.
4. `kg/build_graph.py` projects the same registry into a NetworkX `MultiDiGraph` (~2,700 nodes / ~3,000 edges) and ships a JSON snapshot for the UI.
5. The FastAPI service exposes the registry, the DQ executor, and the KG over HTTP for downstream tools.

To add a new subdomain: drop a YAML file in `data/taxonomy/` matching the schema. That's it.

## Routes the explorer ships with

- `/` and `/v/<vertical>` — verticals + subdomain detail.
- `/governance`, `/catalog`, `/glossary`, `/lineage`, `/dq` — governance backbone.
- `/kg` — vertical-filterable subgraph rendered straight from `kg/graph.json` (click a node to see its 1-hop neighbourhood).
- `/demo` and `/demo/<vertical>` — 3-screen scripted tours per vertical (persona pain → answer + lineage → platform stack).
- `/assistant` — multi-provider assistant grounded by the KG. Routes through a vendor-agnostic abstraction (Claude / GPT / Gemini / Llama via LiteLLM) with automatic failover, an in-memory response cache (sub-100ms on repeats), inline `[REF:<id>]` citations rendered as chips, and a 50-entry canned-answer set in `data/canned-answers.json` as a bulletproof offline fallback. See `apps/explorer-web/lib/llm/` for the provider chain.

## Tests

```bash
# Python (pytest, ~36 tests by default; -m slow runs the full generator suite)
python -m pytest

# TypeScript (vitest, ~15 tests)
pnpm --filter explorer-web test
```

## Running dbt against the populated DuckDB

A real dbt project lives at `modeling/dbt/` for the Payments anchor: 10 staging
views, a small Vault layer (hubs, links, sat as ephemeral CTEs), and a
six-table star (dim_customer, dim_merchant, dim_date, fct_payments,
fct_settlements, fct_chargebacks).

```bash
# from the repo root, after demo-prep has populated domain-explorer.duckdb
npm run dbt:build      # dbt deps && dbt run --select payments+
npm run dbt:test       # dbt test --select payments+
```

The marts land in `domain-explorer.duckdb` under the `dbt` schema. See
`modeling/dbt/README.md` for env-var / sandbox details.

## License

MIT — see `LICENSE`.
