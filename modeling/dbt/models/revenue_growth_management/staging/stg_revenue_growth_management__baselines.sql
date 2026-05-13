{{ config(materialized='view') }}

select
    cast(baseline_id                  as varchar)   as baseline_id,
    cast(account_id                   as varchar)   as account_id,
    cast(pack_id                      as varchar)   as pack_id,
    cast(week_start_date              as date)      as week_start_date,
    cast(baseline_units               as bigint)    as baseline_units,
    cast(baseline_net_revenue_cents   as bigint)    as baseline_net_revenue_cents,
    cast(model_name                   as varchar)   as model_name,
    cast(model_version                as varchar)   as model_version,
    cast(confidence_band_low_units    as bigint)    as confidence_band_low_units,
    cast(confidence_band_high_units   as bigint)    as confidence_band_high_units,
    cast(generated_at                 as timestamp) as generated_at
from {{ source('revenue_growth_management', 'baseline') }}
