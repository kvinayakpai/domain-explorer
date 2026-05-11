-- Staging: light typing on smart_metering.asset_register.
{{ config(materialized='view') }}

select
    cast(asset_id             as varchar) as asset_id,
    cast(asset_type           as varchar) as asset_type,
    cast(make                 as varchar) as make,
    cast(voltage_class_kv     as double)  as voltage_class_kv,
    cast(kva_rating           as integer) as kva_rating,
    cast(feeder_id            as varchar) as feeder_id,
    cast(install_date         as date)    as install_date,
    cast(last_inspection_date as date)    as last_inspection_date,
    cast(condition_score      as double)  as condition_score
from {{ source('smart_metering', 'asset_register') }}
