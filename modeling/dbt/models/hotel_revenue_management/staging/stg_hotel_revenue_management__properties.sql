-- Staging: hotel property master.
{{ config(materialized='view') }}

select
    cast(property_id as varchar) as property_id,
    cast(name        as varchar) as property_name,
    cast(city        as varchar) as city,
    upper(country)               as country_code,
    cast(brand       as varchar) as brand,
    cast(stars       as integer) as stars,
    cast(rooms       as integer) as room_count,
    cast(active      as boolean) as is_active
from {{ source('hotel_revenue_management', 'properties') }}
