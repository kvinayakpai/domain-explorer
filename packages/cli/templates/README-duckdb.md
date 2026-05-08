# Cloud target: DuckDB (${customer})

This clone runs against the file-based DuckDB store the source repo ships with.
That's perfect for a local demo — every query is sub-millisecond and you don't
need any cloud credentials.

## Switching to a real warehouse

Re-run the Customer Accelerator CLI with a different `--cloud`:

```bash
npx @domain-explorer/init ${customer} --cloud=snowflake
# or --cloud=bigquery / --cloud=databricks / --cloud=postgres
```

That writes the appropriate `profiles-*.yml` next to this file. Move it (or
its contents) into `~/.dbt/profiles.yml` and update `.env.local` with the
credentials referenced by the profile.
