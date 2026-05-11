-- Staging: light typing on smart_metering.meter_read; adds a date_key helper.
{{ config(materialized='view') }}

select
    cast(read_id          as varchar)   as read_id,
    cast(meter_id         as varchar)   as meter_id,
    cast(read_ts          as timestamp) as read_ts,
    cast(obis_code        as varchar)   as obis_code,
    cast(interval_minutes as integer)   as interval_minutes,
    cast(kwh_delivered    as double)    as kwh_delivered,
    cast(kwh_received     as double)    as kwh_received,
    cast(voltage_v        as double)    as voltage_v,
    cast(current_a        as double)    as current_a,
    cast(power_factor     as double)    as power_factor,
    cast(quality_code     as varchar)   as quality_code,
    cast({{ format_date('read_ts', '%Y%m%d') }} as integer) as read_date_key
from {{ source('smart_metering', 'meter_read') }}
