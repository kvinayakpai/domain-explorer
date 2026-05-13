-- Fact — competitive price observations.
-- Pre-computes CPI (own_price / observed_price) using the most recent regular
-- own price for the SKU at any store in the same week.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_pricing_and_promotions__competitive_price') }}),
     prd as (select * from {{ ref('dim_product_pricing') }}),
     pr as (
        select
            product_id,
            avg(amount_minor) as own_price_minor
        from {{ ref('stg_pricing_and_promotions__price') }}
        where price_type = 'regular'
        group by product_id
     )

select
    c.competitive_price_id   as competitive_obs_id,
    cast({{ format_date('c.observed_at', '%Y%m%d') }} as integer) as date_key,
    prd.product_sk,
    c.competitor_id,
    c.competitor_name,
    c.channel,
    c.observed_price_minor,
    cast(pr.own_price_minor as bigint) as own_price_minor,
    case
        when c.observed_price_minor > 0
        then cast(pr.own_price_minor as double) / c.observed_price_minor
        else null
    end                                as cpi,
    c.on_promo,
    c.match_type,
    c.match_confidence,
    c.source,
    c.observed_at
from c
left join prd on prd.product_id = c.product_id
left join pr  on pr.product_id  = c.product_id
