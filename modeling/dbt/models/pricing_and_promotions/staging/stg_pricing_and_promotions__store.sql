{{ config(materialized='view') }}

select
    cast(store_id      as varchar)    as store_id,
    cast(store_name    as varchar)    as store_name,
    cast(banner        as varchar)    as banner,
    cast(price_zone_id as varchar)    as price_zone_id,
    cast(region        as varchar)    as region,
    cast(country_iso2  as varchar)    as country_iso2,
    cast(format        as varchar)    as format,
    cast(open_date     as date)       as open_date,
    cast(status        as varchar)    as status
from {{ source('pricing_and_promotions', 'store') }}
