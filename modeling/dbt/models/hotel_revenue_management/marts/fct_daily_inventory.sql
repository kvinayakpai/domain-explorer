-- Grain: one row per (room_type, stay_date). Joins the daily-pricing table to
-- surface ADR and yield score on the same row, alongside availability.
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_hotel_revenue_management__daily_inventory') }}),
     p as (
         select
             room_type_id,
             stay_date,
             avg(rate)        as avg_rate,
             max(yield_score) as max_yield_score,
             min(rate_plan_id) as sample_rate_plan_id
         from {{ ref('stg_hotel_revenue_management__daily_pricing') }}
         group by room_type_id, stay_date
     ),
     hub_rt as (select * from {{ ref('int_hotel_revenue_management__hub_room_type') }})

select
    md5(i.inv_id)                                       as inventory_key,
    i.inv_id,
    i.room_type_id,
    rt.h_room_type_hk                                   as room_type_key,
    i.stay_date,
    cast(strftime(i.stay_date, '%Y%m%d') as integer)    as stay_date_key,
    i.available_rooms,
    i.sold_rooms,
    i.out_of_order_rooms,
    i.occupancy_pct,
    p.avg_rate,
    p.max_yield_score,
    p.sample_rate_plan_id,
    coalesce(p.avg_rate, 0.0) * coalesce(i.occupancy_pct, 0.0) as revpar
from i
left join p     on p.room_type_id = i.room_type_id and p.stay_date = i.stay_date
left join hub_rt rt on rt.room_type_bk = i.room_type_id
