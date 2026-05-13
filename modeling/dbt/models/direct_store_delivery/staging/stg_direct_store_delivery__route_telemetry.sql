{{ config(materialized='view') }}

select
    cast(telemetry_id     as varchar)  as telemetry_id,
    cast(vehicle_id       as varchar)  as vehicle_id,
    cast(driver_id        as varchar)  as driver_id,
    cast(observed_at      as timestamp) as observed_at,
    cast(lat              as double)   as lat,
    cast(lng              as double)   as lng,
    cast(speed_mph        as double)   as speed_mph,
    cast(heading_deg      as smallint) as heading_deg,
    cast(odometer_miles   as double)   as odometer_miles,
    cast(fuel_pct         as double)   as fuel_pct,
    cast(ignition_on      as boolean)  as ignition_on,
    cast(hos_status       as varchar)  as hos_status,
    cast(harsh_event_type as varchar)  as harsh_event_type,
    case when harsh_event_type is not null then true else false end as is_harsh_event,
    case when speed_mph > 65 then true else false end                as is_over_speed
from {{ source('direct_store_delivery', 'route_telemetry') }}
