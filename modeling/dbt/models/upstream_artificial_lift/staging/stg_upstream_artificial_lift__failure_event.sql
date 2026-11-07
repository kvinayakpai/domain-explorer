{{ config(materialized='view') }}

-- ESP and well failures (ISO 14224).
select
    cast(failure_event_id       as varchar ) as failure_event_id,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(esp_string_id          as varchar ) as esp_string_id,
    cast(failed_on              as date    ) as failed_on,
    cast(iso14224_failure_mode  as varchar ) as iso14224_failure_mode,
    cast(description            as varchar ) as description,
    cast(repair_days            as integer ) as repair_days
from {{ source('upstream_artificial_lift', 'failure_event') }}
