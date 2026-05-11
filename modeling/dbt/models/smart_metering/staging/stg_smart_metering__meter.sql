-- Staging: light typing on smart_metering.meter.
{{ config(materialized='view') }}

select
    cast(meter_id              as varchar) as meter_id,
    cast(serial_number         as varchar) as serial_number,
    cast(service_point_id      as varchar) as service_point_id,
    cast(manufacturer          as varchar) as manufacturer,
    cast(model                 as varchar) as model,
    cast(firmware_version      as varchar) as firmware_version,
    cast(form_factor           as varchar) as form_factor,
    cast(communication_protocol as varchar) as communication_protocol,
    cast(installed_at          as date)    as installed_at,
    cast(ct_ratio              as varchar) as ct_ratio,
    cast(status                as varchar) as status
from {{ source('smart_metering', 'meter') }}
