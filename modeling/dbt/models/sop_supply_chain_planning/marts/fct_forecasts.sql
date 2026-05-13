-- Fact — one row per forecast item-location-customer-period-version.
-- Joins to dim_item_sop, dim_location_sop, dim_customer_sop, dim_sop_cycle,
-- dim_date_sop. Powers Forecast Accuracy (MAPE/WAPE), Bias.
{{ config(materialized='table') }}

with f as (select * from {{ ref('stg_sop_supply_chain_planning__forecasts') }}),
     i as (select * from {{ ref('dim_item_sop') }}),
     l as (select * from {{ ref('dim_location_sop') }}),
     c as (select * from {{ ref('dim_customer_sop') }}),
     y as (select * from {{ ref('dim_sop_cycle') }})

select
    f.forecast_id,
    cast({{ format_date('f.period_start', '%Y%m%d') }} as integer) as date_key,
    i.item_sk,
    l.location_sk,
    c.customer_sk,
    y.cycle_sk,
    f.forecast_version,
    f.period_grain,
    f.forecast_units,
    f.forecast_value                                            as forecast_value_usd,
    f.forecast_low,
    f.forecast_high,
    f.model_id,
    f.locked,
    f.published_at
from f
left join i on i.item_id     = f.item_id
left join l on l.location_id = f.location_id
left join c on c.customer_id = f.customer_id
left join y on y.cycle_id    = f.cycle_id
