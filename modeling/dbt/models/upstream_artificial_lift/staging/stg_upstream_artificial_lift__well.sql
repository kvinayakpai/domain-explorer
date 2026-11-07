{{ config(materialized='view') }}

-- Producing wells and their lift method.
select
    cast(well_id                as varchar ) as well_id,
    cast(functional_location_id as varchar ) as functional_location_id,
    cast(floc_code              as varchar ) as floc_code,
    cast(field_id               as varchar ) as field_id,
    cast(pad                    as varchar ) as pad,
    cast(lift_method            as varchar ) as lift_method,
    cast(esp_position_id        as varchar ) as esp_position_id,
    cast(esp_setting_depth_m    as double  ) as esp_setting_depth_m
from {{ source('upstream_artificial_lift', 'well') }}
