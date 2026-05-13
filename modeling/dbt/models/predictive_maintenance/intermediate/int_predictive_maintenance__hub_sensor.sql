-- Vault hub for the Sensor business key.
{{ config(materialized='ephemeral') }}

with src as (
    select sensor_id
    from {{ ref('stg_predictive_maintenance__sensor') }}
    where sensor_id is not null
)

select
    md5(sensor_id)                      as h_sensor_hk,
    sensor_id                           as sensor_bk,
    current_date                        as load_date,
    'predictive_maintenance.sensor'     as record_source
from src
group by sensor_id
