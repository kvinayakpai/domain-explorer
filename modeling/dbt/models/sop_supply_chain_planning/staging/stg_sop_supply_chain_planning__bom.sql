{{ config(materialized='view') }}

select
    cast(bom_id             as varchar) as bom_id,
    cast(parent_item_id     as varchar) as parent_item_id,
    cast(component_item_id  as varchar) as component_item_id,
    cast(location_id        as varchar) as location_id,
    cast(quantity_per       as double)  as quantity_per,
    cast(yield_pct          as double)  as yield_pct,
    cast(effective_from     as date)    as effective_from,
    cast(effective_to       as date)    as effective_to,
    cast(bom_version        as varchar) as bom_version
from {{ source('sop_supply_chain_planning', 'bom') }}
