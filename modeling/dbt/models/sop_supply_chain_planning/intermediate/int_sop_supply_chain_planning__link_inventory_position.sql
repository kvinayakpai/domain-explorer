-- Vault link: inventory position row keyed by (item, location, snapshot_ts).
{{ config(materialized='ephemeral') }}

with src as (
    select item_id, location_id, snapshot_ts
    from {{ ref('stg_sop_supply_chain_planning__inventory_positions') }}
    where item_id is not null
)

select
    md5(item_id || '|' || coalesce(location_id,'') || '|' || cast(snapshot_ts as varchar))
                                                          as l_inventory_position_hk,
    md5(item_id)                                           as h_item_hk,
    md5(location_id)                                       as h_location_hk,
    snapshot_ts,
    current_date                                           as load_date,
    'sop_supply_chain_planning.inventory_position'         as record_source
from src
