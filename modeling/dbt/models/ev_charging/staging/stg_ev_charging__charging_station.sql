{{ config(materialized='view') }}

select
    cast(station_id       as varchar)   as station_id,
    cast(location_id      as varchar)   as location_id,
    cast(ocpp_endpoint    as varchar)   as ocpp_endpoint,
    cast(vendor           as varchar)   as vendor,
    cast(model            as varchar)   as model,
    cast(firmware_version as varchar)   as firmware_version,
    cast(ocpp_version     as varchar)   as ocpp_version,
    cast(registered_at    as timestamp) as registered_at,
    cast(last_heartbeat_ts as timestamp) as last_heartbeat_ts,
    cast(status           as varchar)   as status
from {{ source('ev_charging', 'charging_station') }}
