-- Vault satellite carrying time-phased forecast value attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_sop_supply_chain_planning__forecasts') }})

select
    md5(item_id || '|' || coalesce(location_id,'') || '|' || coalesce(customer_id,'')
        || '|' || coalesce(cycle_id,'') || '|' || coalesce(forecast_version,'')
        || '|' || cast(period_start as varchar))                            as l_forecast_hk,
    cast(published_at as timestamp)                                         as load_ts,
    md5(cast(forecast_units as varchar) || '|' || cast(forecast_value as varchar)
        || '|' || coalesce(model_id,'') || '|' || cast(locked as varchar))  as hashdiff,
    forecast_units,
    forecast_value,
    forecast_low,
    forecast_high,
    model_id,
    locked,
    'sop_supply_chain_planning.forecast'                                    as record_source
from src
