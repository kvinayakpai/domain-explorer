{{ config(materialized='view') }}

select
    cast(price_zone_id    as varchar)  as price_zone_id,
    cast(zone_name        as varchar)  as zone_name,
    cast(pricing_strategy as varchar)  as pricing_strategy,
    cast(tier             as varchar)  as tier
from {{ source('pricing_and_promotions', 'price_zone') }}
