-- Location dimension. Suffix `_sop` avoids collision with other anchors' dim_location.
{{ config(materialized='table') }}

select
    row_number() over (order by location_id) as location_sk,
    location_id,
    gln,
    location_type,
    country_iso2,
    region,
    tier,
    time_zone,
    status
from {{ ref('stg_sop_supply_chain_planning__locations') }}
