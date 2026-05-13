-- Fact — one row per price snapshot.
-- Grain: price_id (a single effective-dated price event).
{{ config(materialized='table') }}

with p as (select * from {{ ref('stg_pricing_and_promotions__price') }}),
     prd as (select * from {{ ref('dim_product_pricing') }}),
     str as (select * from {{ ref('dim_store_pricing') }}),
     et as (select * from {{ ref('dim_price_event_type') }})

select
    p.price_id                                                                              as price_event_id,
    cast({{ format_date('p.effective_from', '%Y%m%d') }} as integer)                         as date_key,
    prd.product_sk,
    str.store_sk,
    et.price_event_type_sk,
    p.amount_minor,
    p.currency,
    case p.currency
        when 'USD' then p.amount_minor / 100.0
        when 'EUR' then p.amount_minor / 100.0 * 1.08
        when 'GBP' then p.amount_minor / 100.0 * 1.27
        when 'CAD' then p.amount_minor / 100.0 * 0.74
        else p.amount_minor / 100.0
    end                                                                                     as amount_usd,
    p.prior_30day_low_minor,
    p.effective_from,
    p.effective_to,
    et.is_promotional,
    et.is_markdown,
    p.source_system
from p
left join prd on prd.product_id = p.product_id
left join str on str.store_id   = p.store_id
left join et  on et.price_type  = p.price_type
