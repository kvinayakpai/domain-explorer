-- Vault-style satellite for Forecast attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_demand_planning__forecasts') }}
)

select
    md5(forecast_id)                                          as h_forecast_hk,
    generated_at                                              as load_ts,
    md5(coalesce(model,'') || '|' || cast(forecast_qty as varchar)
        || '|' || cast(horizon_weeks as varchar))             as hashdiff,
    item_id,
    location_id,
    horizon_weeks,
    model,
    forecast_qty,
    lower_80,
    upper_80,
    pi_relative_width,
    'demand_planning.forecasts'                               as record_source
from src
