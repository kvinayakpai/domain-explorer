# dbt — multi-anchor models

DuckDB-backed dbt project. Five anchors are wired against the populated
`domain-explorer.duckdb` at the repo root: **Payments**, **P&C Claims**,
**Merchandising**, **Demand Planning**, and **Hotel Revenue Management**.
Other subdomains remain documentation-only DDL under `modeling/ddl/`.

## Layout

```
modeling/dbt/
  dbt_project.yml             # materialisation defaults per layer per anchor
  profiles.yml                # local DuckDB profile (uses DOMAIN_EXPLORER_DUCKDB)
  packages.yml                # dbt-utils
  models/
    payments/                       # 10 stg + 6 int + 6 mart  (39 tests)
    p_and_c_claims/                 # 10 stg + 6 int + 10 mart
    merchandising/                  # 10 stg + 5 int + 9 mart
    demand_planning/                # 10 stg + 5 int + 8 mart
    hotel_revenue_management/       # 10 stg + 5 int + 9 mart
```

Each anchor follows the same shape:

- `sources.yml` — typed sources mapped to the populated DuckDB schemas.
- `staging/` — light typing/renaming views (1:1 with each source table).
- `intermediate/` — Vault-style hubs / links / satellites (ephemeral, CTE-inlined).
- `marts/` — star-schema dims and facts materialised as tables.
- `schema.yml` — `unique` / `not_null` tests on natural and surrogate keys.

Materialisation rules from `dbt_project.yml`:

- `staging`     → `view`
- `intermediate` → `ephemeral` (CTE-inlined, no DB objects)
- `marts`       → `table`

## Pointing dbt at the populated DuckDB

`profiles.yml` resolves the database path from `DOMAIN_EXPLORER_DUCKDB` and
falls back to `../../domain-explorer.duckdb` (correct for `cd modeling/dbt`).

```bash
# repo root → run a one-shot build of every anchor
npm run dbt:build:all

# or build one anchor at a time
npm run dbt:build:payments
npm run dbt:build:p_and_c_claims
npm run dbt:build:merchandising
npm run dbt:build:demand_planning
npm run dbt:build:hotel_revenue_management

# tests follow the same naming
npm run dbt:test:all
npm run dbt:test:p_and_c_claims
# ... etc.

# or call dbt directly
cd modeling/dbt
DBT_PROFILES_DIR=. dbt deps
DBT_PROFILES_DIR=. dbt run  --select p_and_c_claims+
DBT_PROFILES_DIR=. dbt test --select p_and_c_claims+
```

The marts land in `domain-explorer.duckdb` under the `dbt` schema (configured
via `+schema: dbt` in `dbt_project.yml`). The source tables are not touched.

If you want a sandbox copy that doesn't write into the populated DB:

```bash
DOMAIN_EXPLORER_DUCKDB="$(pwd)/sandbox.duckdb" npm run dbt:build:all
```

## Vault-style intermediates

Each anchor uses the same hub / link / satellite pattern from the original
Payments build:

| Anchor                     | Hubs                                       | Links                                                         | Sats                  |
| -------------------------- | ------------------------------------------ | ------------------------------------------------------------- | --------------------- |
| `payments`                 | customer, merchant, payment                 | payment↔customer, payment↔merchant                            | payment               |
| `p_and_c_claims`           | policyholder, policy, claim                 | claim↔policy, policy↔policyholder                             | claim                 |
| `merchandising`            | product, store, vendor                      | product↔vendor                                                | product               |
| `demand_planning`          | item, location, customer                    | demand↔item↔location                                          | forecast              |
| `hotel_revenue_management` | property, room_type, reservation            | reservation↔property↔room_type                                | reservation           |

The hubs are deliberately thin (business key + load metadata) and the
satellites carry a `hashdiff` so downstream incremental loaders can detect
attribute change without re-comparing every column.

## Marts per anchor

The marts layer for each anchor follows the same star-schema shape:

| Anchor                     | Dimensions                                                                  | Facts                                                                                                          |
| -------------------------- | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `payments`                 | dim_customer, dim_merchant, dim_date                                        | fct_payments, fct_settlements, fct_chargebacks                                                                 |
| `p_and_c_claims`           | dim_policyholder, dim_policy, dim_claim, dim_adjuster, dim_date             | fct_claims, fct_claims_daily, fct_payments, fct_claim_payments, fct_reserves                                   |
| `merchandising`            | dim_product, dim_store, dim_vendor, dim_date                                | fct_sales, fct_sales_daily, fct_inventory_snapshots, fct_returns, fct_markdowns                                |
| `demand_planning`          | dim_item, dim_location, dim_date                                            | fct_demand, fct_forecast, fct_forecast_accuracy, fct_shipments, fct_inventory_positions                        |
| `hotel_revenue_management` | dim_property, dim_room_type, dim_rate_plan, dim_guest, dim_channel, dim_date | fct_reservations, fct_daily_inventory, fct_daily_revenue                                                       |

`fct_claim_payments` is kept alongside the brief-aligned `fct_payments`
for back-compatibility with existing dashboards built on the original
mart name. New work should target `fct_payments`.

## Lineage

The Payments lineage diagram in the explorer (`/lineage`) is hand-curated
to match the structure under `payments/`. The four new anchors are wired
through `sources.yml` → staging → vault → marts the same way; if you
extend the explorer's lineage diagram for them, follow the same node /
edge pattern in `apps/explorer-web/components/lineage-diagram.tsx`.
