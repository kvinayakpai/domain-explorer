-- Item dimension. Suffix `_sop` avoids collision with other anchors' dim_item.
{{ config(materialized='table') }}

select
    row_number() over (order by item_id)        as item_sk,
    item_id,
    gtin,
    sku,
    item_family,
    item_class,
    xyz_class,
    lifecycle_stage,
    uom_base,
    planning_uom,
    unit_cost,
    unit_price,
    shelf_life_days,
    status,
    cast(created_at as timestamp)               as valid_from,
    cast(null as timestamp)                     as valid_to,
    true                                        as is_current
from {{ ref('stg_sop_supply_chain_planning__items') }}
