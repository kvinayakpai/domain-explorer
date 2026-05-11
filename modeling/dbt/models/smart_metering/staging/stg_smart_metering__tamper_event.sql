-- Staging: light typing on smart_metering.tamper_event.
{{ config(materialized='view') }}

select
    cast(tamper_id          as varchar)   as tamper_id,
    cast(meter_id           as varchar)   as meter_id,
    cast(detected_at        as timestamp) as detected_at,
    cast(tamper_type        as varchar)   as tamper_type,
    cast(severity           as varchar)   as severity,
    cast(field_validated    as boolean)   as is_field_validated,
    cast(energy_loss_kwh_est as double)   as energy_loss_kwh_est,
    cast(status             as varchar)   as status,
    cast({{ format_date('detected_at', '%Y%m%d') }} as integer) as detected_date_key
from {{ source('smart_metering', 'tamper_event') }}
