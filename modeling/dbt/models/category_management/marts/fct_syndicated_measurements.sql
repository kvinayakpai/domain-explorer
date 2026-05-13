-- Fact — syndicated POS / panel measurement at SKU × store × week grain.
{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_category_management__syndicated_measurements') }}),
     p as (select * from {{ ref('dim_product_cm') }}),
     st as (select * from {{ ref('dim_store_cm') }}),
     c as (select * from {{ ref('dim_category') }})

select
    s.measurement_id,
    cast({{ format_date('s.week_start_date', '%Y%m%d') }} as integer) as date_key,
    p.product_sk,
    st.store_sk,
    c.category_sk,
    s.week_start_date,
    s.geography,
    s.units_sold,
    s.dollars_sold_cents,
    s.avg_retail_price_cents,
    s.market_share_pct,
    s.penetration_pct,
    s.buy_rate_units,
    s.any_promo_flag,
    s.source,
    s.panel_id,
    s.projection_factor
from s
left join p  on p.sku_id      = s.sku_id
left join st on st.store_id   = s.store_id
left join c  on c.category_id = s.category_id
