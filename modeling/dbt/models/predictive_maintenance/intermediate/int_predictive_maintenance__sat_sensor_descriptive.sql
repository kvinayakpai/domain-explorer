-- Vault satellite carrying mutable Sensor attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_predictive_maintenance__sensor') }})

select
    md5(sensor_id)                                                              as h_sensor_hk,
    cast(install_date as timestamp)                                             as load_ts,
    md5(coalesce(sensor_type,'') || '|' || coalesce(measurement_location,'')
        || '|' || coalesce(unit,'') || '|' || cast(coalesce(sampling_hz, 0) as varchar)
        || '|' || cast(coalesce(alarm_high, 0) as varchar)
        || '|' || coalesce(status,''))                                          as hashdiff,
    sensor_type,
    measurement_location,
    unit,
    sampling_hz,
    range_min,
    range_max,
    alarm_low,
    alarm_high,
    status,
    'predictive_maintenance.sensor'                                             as record_source
from src
