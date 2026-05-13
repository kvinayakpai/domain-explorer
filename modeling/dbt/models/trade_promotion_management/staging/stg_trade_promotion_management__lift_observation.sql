{{ config(materialized='view') }}

select
    cast(lift_observation_id            as varchar) as lift_observation_id,
    cast(tactic_id                      as varchar) as tactic_id,
    cast(account_id                     as varchar) as account_id,
    cast(sku_id                         as varchar) as sku_id,
    cast(week_start_date                as date)    as week_start_date,
    cast(actual_units                   as bigint)  as actual_units,
    cast(baseline_units                 as bigint)  as baseline_units,
    cast(incremental_units              as bigint)  as incremental_units,
    cast(lift_pct                       as double)  as lift_pct,
    cast(cannibalization_units          as bigint)  as cannibalization_units,
    cast(halo_units                     as bigint)  as halo_units,
    cast(incremental_gross_profit_cents as bigint)  as incremental_gross_profit_cents,
    cast(actual_roi                     as double)  as actual_roi,
    cast(source                         as varchar) as source
from {{ source('trade_promotion_management', 'lift_observation') }}
