# dbt — Payments models

DuckDB-backed dbt project. The Payments anchor is fully wired against the
populated `domain-explorer.duckdb` at the repo root; other subdomains are still
documentation-only DDL under `modeling/ddl/`.

## Layout

```
modeling/dbt/
  dbt_project.yml             # materialisation defaults per layer
  profiles.yml                # local DuckDB profile (uses