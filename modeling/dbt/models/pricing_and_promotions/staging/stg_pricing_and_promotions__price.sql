{{ config(materialized='view') }}

select
    cast(price_id                as varchar)    as price_id,
    cast(product_id              as varchar)    as product_id,
    cast(store_id                as varchar)    as store_id,
    cast(price_zone_id           as varchar)    as price_zone_id,
    cast(price_type              as varchar)    as price_type,
    cast(amount                  as double)     as amount,
    cast(currency                as varchar)    as currency,
    cast(effective_from          as timestamp)  as effective_from,
    cast(effective_to            as timestamp)  as effective_to,
    cast(source_system           as varchar)    as source_system,
    cast(prior_30day_low_minor   as bigint)     as prior_30day_low_minor,
    cast(status                  as varchar)    as status,
    cast(round(amount * 100) as bigint)         as amount_minor
from {{ source('pricing_and_promotions', 'price') }}
