{{ config(materialized='view') }}

select
    cast(location_id        as varchar) as location_id,
    cast(cpo_id             as varchar) as cpo_id,
    cast(name               as varchar) as location_name,
    cast(address_line       as varchar) as address_line,
    cast(city               as varchar) as city,
    cast(postal_code        as varchar) as postal_code,
    upper(country_code)                 as country_code,
    cast(latitude           as double)  as latitude,
    cast(longitude          as double)  as longitude,
    cast(parking_type       as varchar) as parking_type,
    cast(operational_status as varchar) as operational_status
from {{ source('ev_charging', 'location') }}
