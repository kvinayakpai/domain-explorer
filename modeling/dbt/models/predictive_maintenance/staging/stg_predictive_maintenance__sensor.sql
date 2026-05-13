{{ config(materialized='view') }}

select
    cast(sensor_id              as varchar)    as sensor_id,
    cast(asset_id               as varchar)    as asset_id,
    cast(sensor_type            as varchar)    as sensor_type,
    cast(measurement_location   as varchar)    as measurement_location,
    cast(unit                   as varchar)    as unit,
    cast(sampling_hz            as double)     as sampling_hz,
    cast(range_min              as double)     as range_min,
    cast(range_max              as double)     as range_max,
    cast(alarm_low              as double)     as alarm_low,
    cast(alarm_high             as double)     as alarm_high,
    cast(install_date           as date)       as install_date,
    cast(status                 as varchar)    as status
from {{ source('predictive_maintenance', 'sensor') }}
