-- Promo dimension.
{{ config(materialized='table') }}

select
    row_number() over (order by promo_id)    as promo_sk,
    promo_id,
    promo_name,
    mechanic,
    discount_pct,
    discount_amount_minor,
    start_ts,
    end_ts,
    funding_source,
    trade_spend_minor,
    vendor_id,
    status,
    created_at
from {{ ref('stg_pricing_and_promotions__promo') }}
