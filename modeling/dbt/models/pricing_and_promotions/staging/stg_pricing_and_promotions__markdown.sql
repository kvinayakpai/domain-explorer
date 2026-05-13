{{ config(materialized='view') }}

select
    cast(markdown_id              as varchar)    as markdown_id,
    cast(product_id               as varchar)    as product_id,
    cast(store_id                 as varchar)    as store_id,
    cast(pre_price_minor          as bigint)     as pre_price_minor,
    cast(post_price_minor         as bigint)     as post_price_minor,
    cast(markdown_depth_pct       as double)     as markdown_depth_pct,
    cast(reason_code              as varchar)    as reason_code,
    cast(optimizer                as varchar)    as optimizer,
    cast(triggered_at             as timestamp)  as triggered_at,
    cast(effective_from           as timestamp)  as effective_from,
    cast(effective_to             as timestamp)  as effective_to,
    cast(planned_sell_through_pct as double)     as planned_sell_through_pct,
    cast(actual_sell_through_pct  as double)     as actual_sell_through_pct
from {{ source('pricing_and_promotions', 'markdown') }}
