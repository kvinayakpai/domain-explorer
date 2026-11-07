-- One row per functional failure, with the pump's lots and days since installation.
{{ config(materialized='table') }}

select
    f.failure_event_id,
    f.functional_location_id              as functional_location_key,
    f.equipment_id                        as equipment_key,
    f.failed_on,
    f.iso14224_failure_mode,
    f.repair_days,
    f.unit_swapped,
    date_diff('day', i.installed_from, f.failed_on) as days_since_install,
    e.bearing_lot_id,
    e.bearing_lot_waived
from {{ ref('stg_refinery_operations__failure_event') }} f
left join {{ ref('stg_refinery_operations__installation') }} i using (installation_id)
left join {{ ref('dim_equipment_ro') }} e on e.equipment_key = f.equipment_id
