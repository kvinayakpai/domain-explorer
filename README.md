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
│   ├── taxonomy/           # subdomain configs (10 seeded)
│   ├── kpis/               # starter KPI registry
│   ├── source-systems/     # source system registry
│   └── connectors/         # 23 connector patterns
├── modeling/
│   ├── dbt/                # dbt-core skeleton (DuckDB profile)
│   └── ddl/                # 3NF / Vault / dim DDL excerpts
├── kg/
│   ├── ontology/           # OWL/Turtle stubs
│   └── cypher/             # openCypher query templates
├── synthetic-data/         # generation strategy (stub)
├── docs/
│   ├── blueprint/          # drop the project blueprint .docx here
│   └── architecture/       # ADRs
└── .github/workflows/      # CI: node + python lint/typecheck
```

## Quick start (after extracting and running `bootstrap.ps1`)

Prerequisites: Node 20+, pnpm 9+, Python 3.11+, [uv](https://docs.astral.sh/uv/).

```bash
# install JS deps
pnpm install

# install Python deps
uv sync

# run the web app
pnpm --filter explorer-web dev

# run the API
uv run uvicorn app.main:app --reload --app-dir services/api
```

Then open <http://localhost:3000>.

## How the metadata-driven model works

1. YAML files in `data/taxonomy/` define subdomains.
2. `packages/metadata` validates them against Zod (TS) and Pydantic v2 (Python) schemas.
3. The Next.js app reads the typed registry at build/request time and renders the 9-attribute template for every subdomain — no per-page code.
4. The FastAPI service exposes the same registry over HTTP for downstream tools.

To add a new subdomain: drop a YAML file in `data/taxonomy/` matching the schema. That's it.

## License

MIT — see `LICENSE`.
