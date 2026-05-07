-- Staging: inventory snapshots.
{{ config(materialized='view') }}

select
    cast(snapshot_id   as varchar)   as snapshot_id,
    cast(sku           as varchar)   as sku,
    cast(store_id      as varchar)   as store_id,
    cast(on_hand       as integer)   as on_hand,
    cast(on_order      as integer)   as on_order,
    cast(safety_stock  as integer)   as safety_stock,
    cast(as_of         as timestamp) as as_of,
    case
        when cast(safety_stock as integer) > 0
         and cast(on_hand as integer) < cast(safety_stock as integer)
            then true else false
    end                              as is_below_safety
from {{ source('merchandising', 'inventory_snapshots') }}
