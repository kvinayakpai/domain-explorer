-- Staging: plant master.
{{ config(materialized='view') }}

select
    cast(plant_id   as varchar) as plant_id,
    cast(plant_name as varchar) as plant_name,
    upper(country)              as country_iso2,
    cast(region     as varchar) as region,
    cast(size_sqm   as integer) as size_sqm,
    cast(active     as boolean) as active
from {{ source('mes_quality', 'plants') }}
