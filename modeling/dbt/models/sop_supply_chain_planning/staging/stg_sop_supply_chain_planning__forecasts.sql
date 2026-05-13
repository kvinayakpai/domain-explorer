{{ config(materialized='view') }}

select
    cast(forecast_id      as bigint)   as forecast_id,
    cast(item_id          as varchar)  as item_id,
    cast(location_id      as varchar)  as location_id,
    cast(customer_id      as varchar)  as customer_id,
    cast(forecast_version as varchar)  as forecast_version,
    cast(cycle_id         as varchar)  as cycle_id,
    cast(period_start     as date)     as period_start,
    cast(period_grain     as varchar)  as period_grain,
    cast(forecast_units   as double)   as forecast_units,
    cast(forecast_value   as double)   as forecast_value,
    cast(forecast_low     as double)   as forecast_low,
    cast(forecast_high    as double)   as forecast_high,
    cast(model_id         as varchar)  as model_id,
    cast(published_at     as timestamp) as published_at,
    cast(locked           as boolean)  as locked
from {{ source('sop_supply_chain_planning', 'forecast') }}
