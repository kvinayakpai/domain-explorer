-- Grain: one row per forecast prediction (item, location, horizon, model).
-- Surfaces forecast quantity + 80% prediction interval and propagates
-- conformed item / location keys.
{{ config(materialized='table') }}

with f as (select * from {{ ref('stg_demand_planning__forecasts') }}),
     hub_i as (select * from {{ ref('int_demand_planning__hub_item') }}),
     hub_l as (select * from {{ ref('int_demand_planning__hub_location') }})

select
    md5(f.forecast_id)                                    as forecast_key,
    f.forecast_id,
    f.item_id,
    i.h_item_hk                                           as item_key,
    f.location_id,
    l.h_location_hk                                       as location_key,
    f.horizon_weeks,
    f.model,
    f.forecast_qty,
    f.lower_80,
    f.upper_80,
    f.upper_80 - f.lower_80                               as pi_width,
    f.pi_relative_width,
    case
        when f.pi_relative_width is null              then 'unknown'
        when f.pi_relative_width <= 0.20              then 'tight'
        when f.pi_relative_width <= 0.50              then 'moderate'
        else 'wide'
    end                                                   as pi_band,
    f.generated_at,
    cast({{ format_date('f.generated_at', '%Y%m%d') }} as integer)   as generated_date_key,
    cast(f.generated_at as date)                          as generated_date
from f
left join hub_i i on i.item_bk     = f.item_id
left join hub_l l on l.location_bk = f.location_id
