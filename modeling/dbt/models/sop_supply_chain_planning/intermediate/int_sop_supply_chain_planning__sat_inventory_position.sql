-- Vault satellite carrying inventory-position snapshot attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_sop_supply_chain_planning__inventory_positions') }})

select
    md5(item_id || '|' || coalesce(location_id,'') || '|' || cast(snapshot_ts as varchar))
                                                                         as l_inventory_position_hk,
    cast(snapshot_ts as timestamp)                                       as load_ts,
    md5(cast(on_hand_units as varchar) || '|' || cast(allocated_units as varchar)
        || '|' || cast(safety_stock_units as varchar)
        || '|' || cast(stockout_flag as varchar))                        as hashdiff,
    on_hand_units,
    on_order_units,
    in_transit_units,
    allocated_units,
    safety_stock_units,
    reorder_point_units,
    inventory_value,
    doh_days,
    excess_units,
    stockout_flag,
    'sop_supply_chain_planning.inventory_position'                       as record_source
from src
