-- Staging: light typing on smart_metering.outage_event.
{{ config(materialized='view') }}

select
    cast(outage_id                  as varchar)   as outage_id,
    cast(feeder_id                  as varchar)   as feeder_id,
    cast(service_point_id           as varchar)   as service_point_id,
    cast(started_at                 as timestamp) as started_at,
    cast(restored_at                as timestamp) as restored_at,
    cast(duration_minutes           as integer)   as duration_minutes,
    cast(cause_code                 as varchar)   as cause_code,
    cast(customers_affected         as integer)   as customers_affected,
    cast(saidi_minutes_contribution as double)    as saidi_minutes_contribution,
    cast({{ format_date('started_at', '%Y%m%d') }} as integer) as started_date_key
from {{ source('smart_metering', 'outage_event') }}
