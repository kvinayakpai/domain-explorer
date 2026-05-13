-- Fact — inventory position per item-location-snapshot.
-- Suffix `_sop` avoids collision with other anchors' fct_inventory_position.
{{ config(materialized='table') }}

with p as (select * from {{ ref('stg_sop_supply_chain_planning__inventory_positions') }}),
     i as (select * from {{ ref('dim_item_sop') }}),
     l as (select * from {{ ref('dim_location_sop') }})

select
    p.inventory_position_id,
    cast({{ format_date('cast(p.snapshot_ts as date)', '%Y%m%d') }} as integer) as date_key,
    i.item_sk,
    l.location_sk,
    p.on_hand_units,
    p.on_order_units,
    p.in_transit_units,
    p.allocated_units,
    p.safety_stock_units,
    p.reorder_point_units,
    p.inventory_value                            as inventory_value_usd,
    p.doh_days,
    p.excess_units,
    p.stockout_flag,
    p.snapshot_ts
from p
left join i on i.item_id     = p.item_id
left join l on l.location_id = p.location_id
