{{ config(materialized='view') }}

select
    cast(connector_id        as varchar) as connector_id,
    cast(station_id          as varchar) as station_id,
    cast(evse_id             as varchar) as evse_id,
    cast(connector_position  as integer) as connector_position,
    cast(connector_type      as varchar) as connector_type,
    cast(power_type          as varchar) as power_type,
    cast(max_power_kw        as double)  as max_power_kw,
    cast(voltage_v           as integer) as voltage_v,
    cast(amperage_a          as integer) as amperage_a,
    cast(status              as varchar) as status
from {{ source('ev_charging', 'connector') }}
