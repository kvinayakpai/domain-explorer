{{ config(materialized='view') }}

-- SAP PM notifications (M1/M2).
select
    cast(notification_id        as varchar ) as notification_id,
    cast(notification_type      as varchar ) as notification_type,
    cast(priority               as integer ) as priority,
    cast(status                 as varchar ) as status,
    cast(reported_on            as date    ) as reported_on,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(equipment_id           as varchar ) as equipment_id,
    cast(short_text             as varchar ) as short_text,
    cast(iso14224_failure_mode  as varchar ) as iso14224_failure_mode,
    cast(failure_event_id       as varchar ) as failure_event_id
from {{ source('refinery_operations', 'notification') }}
