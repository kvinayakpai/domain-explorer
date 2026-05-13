-- Grain: one row per inventory position observation.
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_demand_planning__inventory_positions') }}),
     hub_i as (select * from {{ ref('int_demand_planning__hub_item') }}),
     hub_l as (select * from {{ ref('int_demand_planning__hub_location') }})

select
    md5(i.position_id)                                as position_key,
    i.position_id,
    i.item_id,
    hi.h_item_hk                                      as item_key,
    i.location_id,
    hl.h_location_hk                                  as location_key,
    i.on_hand,
    i.in_transit,
    i.reserved,
    i.available_position,
    i.as_of,
    cast({{ format_date('i.as_of', '%Y%m%d') }} as integer)      as as_of_date_key
from i
left join hub_i hi on hi.item_bk     = i.item_id
left join hub_l hl on hl.location_bk = i.location_id
