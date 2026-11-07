{{ config(materialized='view') }}

-- Workover rigs and when each is free.
select
    cast(rig_id    as varchar ) as rig_id,
    cast(field_id  as varchar ) as field_id,
    cast(free_from as date    ) as free_from,
    cast(note      as varchar ) as note
from {{ source('upstream_artificial_lift', 'workover_rig') }}
