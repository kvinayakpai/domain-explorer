-- Grain: one row per historical demand observation.
{{ config(materialized='table') }}

with d as (select * from {{ ref('stg_demand_planning__historical_demand') }}),
     hub_i as (select * from {{ ref('int_demand_planning__hub_item') }}),
     hub_l as (select * from {{ ref('int_demand_planning__hub_location') }}),
     items as (select * from {{ ref('stg_demand_planning__items') }})

select
    md5(d.demand_id)                                    as demand_key,
    d.demand_id,
    d.item_id,
    i.h_item_hk                                         as item_key,
    d.location_id,
    l.h_location_hk                                     as location_key,
    d.period_date,
    cast(strftime(d.period_date, '%Y%m%d') as integer)  as period_date_key,
    d.quantity,
    d.channel,
    coalesce(it.unit_cost, 0.0) * d.quantity            as demand_value
from d
left join hub_i i  on i.item_bk     = d.item_id
left join hub_l l  on l.location_bk = d.location_id
left join items it on it.item_id    = d.item_id
