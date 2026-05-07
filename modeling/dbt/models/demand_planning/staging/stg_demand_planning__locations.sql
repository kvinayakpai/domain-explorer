-- Staging: planning locations.
{{ config(materialized='view') }}

select
    cast(location_id   as varchar) as location_id,
    cast(location_name as varchar) as location_name,
    cast(type          as varchar) as location_type,
    upper(country)                 as country_code,
    cast(capacity_units as integer) as capacity_units
from {{ source('demand_planning', 'locations') }}
