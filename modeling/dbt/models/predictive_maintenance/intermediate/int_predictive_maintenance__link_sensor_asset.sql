-- Vault link: Sensor ↔ Asset.
{{ config(materialized='ephemeral') }}

with s as (
    select sensor_id, asset_id
    from {{ ref('stg_predictive_maintenance__sensor') }}
    where sensor_id is not null
)

select
    md5(sensor_id || '|' || coalesce(asset_id, '')) as l_sensor_asset_hk,
    md5(sensor_id)        as h_sensor_hk,
    md5(asset_id)         as h_asset_hk,
    current_date          as load_date,
    'predictive_maintenance.sensor' as record_source
from s
group by sensor_id, asset_id
