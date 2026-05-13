{{ config(materialized='view') }}

select
    cast(competitive_price_id  as varchar)    as competitive_price_id,
    cast(product_id            as varchar)    as product_id,
    cast(competitor_id         as varchar)    as competitor_id,
    cast(competitor_name       as varchar)    as competitor_name,
    cast(channel               as varchar)    as channel,
    cast(observed_price_minor  as bigint)     as observed_price_minor,
    cast(currency              as varchar)    as currency,
    cast(on_promo              as boolean)    as on_promo,
    cast(match_type            as varchar)    as match_type,
    cast(match_confidence      as double)     as match_confidence,
    cast(source                as varchar)    as source,
    cast(observed_at           as timestamp)  as observed_at
from {{ source('pricing_and_promotions', 'competitive_price') }}
