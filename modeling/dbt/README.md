# dbt skeleton

DuckDB-backed dbt-core skeleton. Real models will be added per subdomain in later phases.

## Usage

```bash
# from repo root, point dbt at this profile dir
DBT_PROFILES_DIR=modeling/dbt dbt deps --project-dir modeling/dbt
DBT_PROFILES_DIR=modeling/dbt dbt build --project-dir modeling/dbt
```

The DuckDB file lands in `modeling/dbt/target/domain_explorer.duckdb`.
