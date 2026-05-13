-- Type-2-ish asset dimension. Suffix `_pm` avoids collision with the
-- dim_asset name used elsewhere (e.g. mes_quality).
{{ config(materialized='table') }}

select
    row_number() over (order by asset_id)        as asset_sk,
    asset_id,
    tag_id,
    asset_class,
    manufacturer,
    model_number,
    serial_number,
    site_id,
    area_id,
    line_id,
    criticality,
    design_life_hours,
    rated_kw,
    status,
    cast(install_date as timestamp)              as valid_from,
    cast(null as timestamp)                      as valid_to,
    true                                         as is_current
from {{ ref('stg_predictive_maintenance__asset') }}
