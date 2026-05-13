-- Vault link: forecast row keyed by (item, location, customer, cycle, version, period).
{{ config(materialized='ephemeral') }}

with src as (
    select
        item_id, location_id, customer_id, cycle_id,
        forecast_version, period_start
    from {{ ref('stg_sop_supply_chain_planning__forecasts') }}
    where item_id is not null
)

select
    md5(item_id || '|' || coalesce(location_id,'') || '|' || coalesce(customer_id,'')
        || '|' || coalesce(cycle_id,'') || '|' || coalesce(forecast_version,'')
        || '|' || cast(period_start as varchar))         as l_forecast_hk,
    md5(item_id)                                          as h_item_hk,
    md5(location_id)                                      as h_location_hk,
    md5(customer_id)                                      as h_customer_hk,
    md5(cycle_id)                                         as h_cycle_hk,
    forecast_version,
    period_start,
    current_date                                          as load_date,
    'sop_supply_chain_planning.forecast'                  as record_source
from src
