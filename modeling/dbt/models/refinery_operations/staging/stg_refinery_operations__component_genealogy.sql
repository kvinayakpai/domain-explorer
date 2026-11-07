{{ config(materialized='view') }}

-- As-built record: lots in each pump serial.
select
    cast(equipment_id   as varchar ) as equipment_id,
    cast(component_kind as varchar ) as component_kind,
    cast(lot_id         as varchar ) as lot_id
from {{ source('refinery_operations', 'component_genealogy') }}
