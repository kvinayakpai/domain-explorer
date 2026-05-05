# Domain Explorer

A metadata-driven explorer for industry verticals, subdomains, KPIs, source systems, and integration patterns. The whole UI is rendered from a typed registry of YAML configs — add a YAML file, get a page.

## What's in here

```
domain-explorer/
├── apps/explorer-web/      # Next.js 14 App Router UI (TS strict, Tailwind, shadcn/ui)
├── services/api/           # FastAPI service (taxonomy + KG queries — stub for now)
├── packages/
│   ├── metadata/           # Zod (TS) + Pydantic v2 (Py) schemas, YAML loader
│   └── shared-types/       # generated TS types
├── data/
│   ├── taxonomy/           # subdomain configs (10 anchors + breadth pass)
│   ├── kpis/               # starter KPI registry
│   ├── source-systems/     # source system registry
│   └── connectors/         # 23 connector patterns
├── modeling/
│   ├── dbt/                # dbt-core skeleton (DuckDB profile)
│   └── ddl/                # 3NF / Vault / dim DDL excerpts (all 7 anchors)
├── kg/
│   ├── ontology/           # OWL/Turtle stubs
│   └── cypher/             # openCypher query templates
├── synthetic-data/         # generation strategy (stub)
├── docs/
│   ├── blueprint/          # drop the project blueprint .docx here
│   └── architecture/       # ADRs
└── .github/workflows/      # CI: node + python lint/typecheck
```

## Quick start

Prerequisites: Node 20+, pnpm 9+, Python 3.10+ (uv optional).

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

# 3. (optional) Enable the live Claude assistant on /assistant.
#    Without this the assistant runs in deterministic demo mode.
cp .env.example .env
# then set ANTHROPIC_API_KEY=sk-ant-...

# 4. (optional) Run the API
uv run uvicorn app.main:app --reload --app-dir services/api
```

Then open <http://localhost:3000>. The subdomain pages will show live numbers from the regenerated DuckDB.

### Why is the data regenerated and not committed?

The full `domain-explorer.duckdb` is ~91MB and the CSV/parquet sidecars push the total over GitHub's 50MB recommended file size. Since the data is fully deterministic (`--seed 42`), it's cheaper to regenerate on first clone than to host it. The local copy is untouched — you only run `demo-prep` on a fresh clone or to refresh a specific subdomain.

## How the metadata-driven model works

1. YAML files in `data/taxonomy/` define subdomains.
2. `packages/metadata` validates them against Zod (TS) and Pydantic v2 (Python) schemas.
3. The Next.js app reads the typed registry at build/request time and renders the 9-attribute template for every subdomain — no per-page code.
4. The FastAPI service exposes the same registry over HTTP for downstream tools.

To add a new subdomain: drop a YAML file in `data/taxonomy/` matching the schema. That's it.

## License

MIT — see `LICENSE`.
