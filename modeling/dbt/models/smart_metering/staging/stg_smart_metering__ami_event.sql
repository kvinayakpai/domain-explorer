-- Staging: light typing on smart_metering.ami_event.
{{ config(materialized='view') }}

select
    cast(event_id    as varchar)   as event_id,
    cast(meter_id    as varchar)   as meter_id,
    cast(event_ts    as timestamp) as event_ts,
    cast(event_code  as varchar)   as event_code,
    cast(event_class as varchar)   as event_class,
    cast(description as varchar)   as event_description,
    cast({{ format_date('event_ts', '%Y%m%d') }} as integer) as event_date_key
from {{ source('smart_metering', 'ami_event') }}
