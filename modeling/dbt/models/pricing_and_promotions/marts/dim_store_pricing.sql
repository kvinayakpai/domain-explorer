-- Store dimension for the pricing anchor — pre-joined to price zone.
-- Suffix `_pricing` avoids collision with other anchors' dim_store.
{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_pricing_and_promotions__store') }}),
     z as (select * from {{ ref('stg_pricing_and_promotions__price_zone') }})

select
    row_number() over (order by s.store_id)        as store_sk,
    s.store_id,
    s.store_name,
    s.banner,
    s.price_zone_id,
    z.zone_name,
    z.pricing_strategy,
    s.region,
    s.country_iso2,
    s.format,
    cast(s.open_date as timestamp)                 as valid_from,
    cast(null as timestamp)                        as valid_to,
    case when s.status = 'active' then true else false end as is_current
from s
left join z on z.price_zone_id = s.price_zone_id
