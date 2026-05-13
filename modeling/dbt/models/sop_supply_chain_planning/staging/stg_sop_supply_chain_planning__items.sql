{{ config(materialized='view') }}

select
    cast(item_id          as varchar)   as item_id,
    cast(gtin             as varchar)   as gtin,
    cast(sku              as varchar)   as sku,
    cast(item_family      as varchar)   as item_family,
    cast(item_class       as varchar)   as item_class,
    cast(xyz_class        as varchar)   as xyz_class,
    cast(lifecycle_stage  as varchar)   as lifecycle_stage,
    cast(uom_base         as varchar)   as uom_base,
    cast(planning_uom     as varchar)   as planning_uom,
    cast(unit_cost        as double)    as unit_cost,
    cast(unit_price       as double)    as unit_price,
    cast(shelf_life_days  as integer)   as shelf_life_days,
    cast(created_at       as timestamp) as created_at,
    cast(status           as varchar)   as status
from {{ source('sop_supply_chain_planning', 'item') }}
