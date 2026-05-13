{{ config(materialized='view') }}

select
    cast(asset_id           as varchar)    as asset_id,
    cast(tag_id             as varchar)    as tag_id,
    cast(asset_class        as varchar)    as asset_class,
    cast(manufacturer       as varchar)    as manufacturer,
    cast(model_number       as varchar)    as model_number,
    cast(serial_number      as varchar)    as serial_number,
    cast(site_id            as varchar)    as site_id,
    cast(area_id            as varchar)    as area_id,
    cast(line_id            as varchar)    as line_id,
    cast(criticality        as varchar)    as criticality,
    cast(install_date       as date)        as install_date,
    cast(design_life_hours  as integer)    as design_life_hours,
    cast(rated_kw           as double)     as rated_kw,
    cast(status             as varchar)    as status
from {{ source('predictive_maintenance', 'asset') }}
