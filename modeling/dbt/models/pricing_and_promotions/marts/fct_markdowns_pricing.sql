-- Fact — markdown events. Naming `_pricing` to avoid colliding with
-- merchandising's potential fct_markdowns.
{{ config(materialized='table') }}

with m as (select * from {{ ref('stg_pricing_and_promotions__markdown') }}),
     prd as (select * from {{ ref('dim_product_pricing') }}),
     str as (select * from {{ ref('dim_store_pricing') }})

select
    m.markdown_id,
    cast({{ format_date('m.triggered_at', '%Y%m%d') }} as integer) as date_key,
    prd.product_sk,
    str.store_sk,
    m.pre_price_minor,
    m.post_price_minor,
    m.markdown_depth_pct,
    m.reason_code,
    m.optimizer,
    m.planned_sell_through_pct,
    m.actual_sell_through_pct,
    -- Regret factor proxy: lost margin from setting markdown too deep too early.
    cast(((m.actual_sell_through_pct - m.planned_sell_through_pct) * m.pre_price_minor) as bigint) as regret_factor_minor,
    m.triggered_at
from m
left join prd on prd.product_id = m.product_id
left join str on str.store_id   = m.store_id
