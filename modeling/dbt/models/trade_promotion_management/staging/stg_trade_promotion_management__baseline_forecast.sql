{{ config(materialized='view') }}

select
    cast(baseline_id            as varchar)   as baseline_id,
    cast(account_id             as varchar)   as account_id,
    cast(sku_id                 as varchar)   as sku_id,
    cast(week_start_date        as date)      as week_start_date,
    cast(baseline_units         as bigint)    as baseline_units,
    cast(baseline_dollars_cents as bigint)    as baseline_dollars_cents,
    cast(model_name             as varchar)   as model_name,
    cast(model_version          as varchar)   as model_version,
    cast(confidence_band_low    as bigint)    as confidence_band_low,
    cast(confidence_band_high   as bigint)    as confidence_band_high,
    cast(generated_at           as timestamp) as generated_at
from {{ source('trade_promotion_management', 'baseline_forecast') }}
