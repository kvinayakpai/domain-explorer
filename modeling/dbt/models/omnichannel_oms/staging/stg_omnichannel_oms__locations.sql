{{ config(materialized='view') }}

select
    cast(location_id              as varchar)    as location_id,
    cast(gln                      as varchar)    as gln,
    cast(name                     as varchar)    as name,
    cast(location_type            as varchar)    as location_type,
    upper(country_iso2)                           as country_iso2,
    cast(region                   as varchar)    as region,
    cast(timezone                 as varchar)    as timezone,
    cast(lat                      as double)     as lat,
    cast(lon                      as double)     as lon,
    cast(bopis_enabled            as boolean)    as bopis_enabled,
    cast(ship_from_enabled        as boolean)    as ship_from_enabled,
    cast(pick_capacity_per_hour   as integer)    as pick_capacity_per_hour,
    cast(status                   as varchar)    as status
from {{ source('omnichannel_oms', 'location') }}
