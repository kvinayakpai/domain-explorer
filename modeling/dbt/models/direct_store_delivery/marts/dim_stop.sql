{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_direct_store_delivery__hub_stop') }}),
     stg as (select * from {{ ref('stg_direct_store_delivery__stop') }})

select
    h.h_stop_hk                                        as stop_sk,
    h.stop_bk                                          as stop_id,
    s.route_id,
    s.outlet_id,
    s.gln,
    cast(strftime(s.route_day, '%Y%m%d') as integer)   as route_day_key,
    s.planned_sequence,
    s.presell_flag
from hub h
left join stg s on s.stop_id = h.stop_bk
