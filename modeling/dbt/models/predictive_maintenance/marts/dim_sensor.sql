{{ config(materialized='table') }}

select
    row_number() over (order by sensor_id)        as sensor_sk,
    sensor_id,
    asset_id,
    sensor_type,
    measurement_location,
    unit,
    sampling_hz,
    range_min,
    range_max,
    alarm_low,
    alarm_high,
    status
from {{ ref('stg_predictive_maintenance__sensor') }}
