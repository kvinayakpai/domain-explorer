{{ config(materialized='table') }}

select
    row_number() over (order by location_id) as location_sk,
    location_id,
    name,
    location_type,
    country_iso2,
    region,
    timezone,
    bopis_enabled,
    ship_from_enabled,
    pick_capacity_per_hour,
    status
from {{ ref('stg_omnichannel_oms__locations') }}
