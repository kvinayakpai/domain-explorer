-- Vault satellite carrying Range Review state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_category_management__range_reviews') }})

select
    md5(range_review_id)                                                              as h_range_review_hk,
    coalesce(created_at, current_timestamp)                                            as load_ts,
    md5(coalesce(status,'') || '|' || cast(coalesce(sku_count_before,0) as varchar) || '|' ||
        cast(coalesce(sku_count_after,0) as varchar))                                  as hashdiff,
    category_id,
    banner,
    cycle_name,
    scheduled_date,
    decision_date,
    in_market_date,
    sku_count_before,
    sku_count_after,
    sku_adds,
    sku_drops,
    forecast_category_sales_delta_cents,
    forecast_margin_delta_cents,
    status,
    led_by,
    'category_management.range_review'                                                 as record_source
from src
