-- Grain: one row per (forecast, error) pair. Surfaces accuracy KPIs and
-- propagates item / location keys for slice-and-dice.
{{ config(materialized='table') }}

with f as (select * from {{ ref('stg_demand_planning__forecasts') }}),
     e as (select * from {{ ref('stg_demand_planning__forecast_errors') }}),
     hub_i as (select * from {{ ref('int_demand_planning__hub_item') }}),
     hub_l as (select * from {{ ref('int_demand_planning__hub_location') }})

select
    md5(e.error_id)                                     as accuracy_key,
    e.error_id,
    e.forecast_id,
    f.item_id,
    i.h_item_hk                                         as item_key,
    f.location_id,
    l.h_location_hk                                     as location_key,
    f.horizon_weeks,
    f.model,
    f.forecast_qty,
    e.actual_qty,
    e.forecast_error,
    e.ape,
    1.0 - e.ape                                         as accuracy_pct,
    e.computed_at,
    cast({{ format_date('e.computed_at', '%Y%m%d') }} as integer)  as computed_date_key,
    f.lower_80,
    f.upper_80,
    case
        when e.actual_qty between f.lower_80 and f.upper_80 then true
        else false
    end                                                 as actual_within_pi
from e
join f on f.forecast_id = e.forecast_id
left join hub_i i on i.item_bk     = f.item_id
left join hub_l l on l.location_bk = f.location_id
