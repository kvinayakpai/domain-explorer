# dbt — Payments models

DuckDB-backed dbt project. The Payments anchor is fully wired against the
populated `domain-explorer.duckdb` at the repo root; other subdomains are still
documentation-only DDL under `modeling/ddl/`.

## Layout

```
modeling/dbt/
  dbt_project.yml             # materialisation defaults per layer
  profiles.yml                # local DuckDB profile (uses DOMAIN_EXPLORER_DUCKDB)
  packages.yml                # dbt-utils
  models/
    payments/
      sources.yml             # 10 sources from the payments schema
      schema.yml              # tests + descriptions on the marts
      staging/                # 10 stg_payments__* views (1:1 with sources)
      intermediate/           # Vault-style hubs / links / sat (ephemeral)
      marts/                  # dim_customer / dim_merchant / dim_date /
                              # fct_payments / fct_settlements / fct_chargebacks
```

Materialisation rules from `dbt_project.yml`:

- `staging`     → `view`
- `intermediate` → `ephemeral` (CTE-inlined, no DB objects)
- `marts`       → `table`

## Pointing dbt at the populated DuckDB

`profiles.yml` resolves the database path from `DOMAIN_EXPLORER_DUCKDB` and
falls back to `../../domain-explorer.duckdb` (correct for `cd modeling/dbt`).

```bash
# repo root → run a one-shot build
npm run dbt:build      # = dbt deps && dbt run --select payments+

# or call dbt directly
cd modeling/dbt
DBT_PROFILES_DIR=. dbt deps
DBT_PROFILES_DIR=. dbt run  --select payments+
DBT_PROFILES_DIR=. dbt test --select payments+
```

The marts land in `domain-explorer.duckdb` under the `dbt` schema (configured
via `+schema: dbt` in `dbt_project.yml`). The source tables are not touched.

If you want a sandbox copy that doesn't write into the populated DB:

```bash
DOMAIN_EXPLORER_DUCKDB="$(pwd)/sandbox.duckdb" npm run dbt:build
```

## Lineage

The Payments lineage diagram in the explorer (`/lineage`) is hand-curated to
match the structure in this folder: 5 source feeds → staging → vault → marts →
KPIs. Adding a new staging or mart model? Add the corresponding node + edge in
`apps/explorer-web/components/lineage-diagram.tsx`.
