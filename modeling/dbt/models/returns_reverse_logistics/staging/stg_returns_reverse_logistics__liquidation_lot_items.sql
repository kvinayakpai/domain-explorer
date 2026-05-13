{{ config(materialized='view') }}

select
    cast(lot_item_id              as varchar)  as lot_item_id,
    cast(lot_id                   as varchar)  as lot_id,
    cast(return_item_id           as varchar)  as return_item_id,
    cast(allocated_cogs_minor     as bigint)   as allocated_cogs_minor,
    cast(allocated_proceeds_minor as bigint)   as allocated_proceeds_minor
from {{ source('returns_reverse_logistics', 'liquidation_lot_item') }}
