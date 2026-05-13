-- Fact — range-review cycle outcomes at the range_review × category grain.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_category_management__range_reviews') }}),
     rr_dim as (select * from {{ ref('dim_range_review') }}),
     c as (select * from {{ ref('dim_category') }})

select
    r.range_review_id,
    rr_dim.range_review_sk,
    c.category_sk,
    cast({{ format_date('r.decision_date', '%Y%m%d') }} as integer) as decision_date_key,
    r.banner,
    r.sku_count_before,
    r.sku_count_after,
    r.sku_adds,
    r.sku_drops,
    (r.sku_count_after - r.sku_count_before)                       as net_sku_delta,
    r.forecast_category_sales_delta_cents,
    r.forecast_margin_delta_cents,
    r.status
from r
left join rr_dim on rr_dim.range_review_id = r.range_review_id
left join c on c.category_id = r.category_id
