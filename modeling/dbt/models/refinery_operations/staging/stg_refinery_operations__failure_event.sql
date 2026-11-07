{{ config(materialized='view') }}

-- Functional failures with ISO 14224 failure mode.
select
    cast(failure_event_id       as varchar ) as failure_event_id,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(equipment_id           as varchar ) as equipment_id,
    cast(installation_id        as varchar ) as installation_id,
    cast(failed_on              as date    ) as failed_on,
    cast(iso14224_failure_mode  as varchar ) as iso14224_failure_mode,
    cast(description            as varchar ) as description,
    cast(repair_days            as integer ) as repair_days,
    cast(unit_swapped           as boolean ) as unit_swapped
from {{ source('refinery_operations', 'failure_event') }}
