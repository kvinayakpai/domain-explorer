{{ config(materialized='view') }}

select
    cast(snapshot_id              as varchar)    as snapshot_id,
    cast(store_id                 as varchar)    as store_id,
    cast(department               as varchar)    as department,
    cast(period_start             as date)       as period_start,
    cast(period_end               as date)       as period_end,
    cast(opening_inventory_minor  as bigint)     as opening_inventory_minor,
    cast(receipts_minor           as bigint)     as receipts_minor,
    cast(cogs_minor               as bigint)     as cogs_minor,
    cast(closing_inventory_minor  as bigint)     as closing_inventory_minor,
    cast(known_shrink_minor       as bigint)     as known_shrink_minor,
    cast(unknown_shrink_minor     as bigint)     as unknown_shrink_minor,
    cast(total_shrink_minor       as bigint)     as total_shrink_minor,
    cast(shrink_pct               as double)     as shrink_pct
from {{ source('loss_prevention', 'shrink_snapshot') }}
