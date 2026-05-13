{{ config(materialized='view') }}

select
    cast(location_id   as varchar) as location_id,
    cast(gln           as varchar) as gln,
    cast(location_type as varchar) as location_type,
    cast(country_iso2  as varchar) as country_iso2,
    cast(region        as varchar) as region,
    cast(tier          as smallint) as tier,
    cast(time_zone     as varchar) as time_zone,
    cast(status        as varchar) as status
from {{ source('sop_supply_chain_planning', 'location') }}
