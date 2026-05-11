-- Staging: sensor readings.
{{ config(materialized='view') }}

select
    cast(reading_id   as varchar)   as reading_id,
    cast(equipment_id as varchar)   as equipment_id,
    cast(metric       as varchar)   as metric,
    cast(value        as double)    as value,
    cast(ts           as timestamp) as ts,
    cast(anomaly      as boolean)   as anomaly
from {{ source('mes_quality', 'sensor_readings') }}
