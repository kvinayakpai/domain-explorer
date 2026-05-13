{{ config(materialized='view') }}

select
    cast(inventory_position_id as bigint)   as inventory_position_id,
    cast(item_id               as varchar)  as item_id,
    cast(location_id           as varchar)  as location_id,
    cast(snapshot_ts           as timestamp) as snapshot_ts,
    cast(on_hand_units         as double)   as on_hand_units,
    cast(on_order_units        as double)   as on_order_units,
    cast(in_transit_units      as double)   as in_transit_units,
    cast(allocated_units       as double)   as allocated_units,
    cast(safety_stock_units    as double)   as safety_stock_units,
    cast(reorder_point_units   as double)   as reorder_point_units,
    cast(inventory_value       as double)   as inventory_value,
    cast(doh_days              as double)   as doh_days,
    cast(excess_units          as double)   as excess_units,
    cast(stockout_flag         as boolean)  as stockout_flag
from {{ source('sop_supply_chain_planning', 'inventory_position') }}
