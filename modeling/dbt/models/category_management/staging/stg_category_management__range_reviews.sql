{{ config(materialized='view') }}

select
    cast(range_review_id                       as varchar)   as range_review_id,
    cast(category_id                           as varchar)   as category_id,
    cast(banner                                as varchar)   as banner,
    cast(cycle_name                            as varchar)   as cycle_name,
    cast(scheduled_date                        as date)      as scheduled_date,
    cast(decision_date                         as date)      as decision_date,
    cast(in_market_date                        as date)      as in_market_date,
    cast(sku_count_before                      as integer)   as sku_count_before,
    cast(sku_count_after                       as integer)   as sku_count_after,
    cast(sku_adds                              as integer)   as sku_adds,
    cast(sku_drops                             as integer)   as sku_drops,
    cast(forecast_category_sales_delta_cents   as bigint)    as forecast_category_sales_delta_cents,
    cast(forecast_margin_delta_cents           as bigint)    as forecast_margin_delta_cents,
    cast(status                                as varchar)   as status,
    cast(led_by                                as varchar)   as led_by,
    cast(created_at                            as timestamp) as created_at
from {{ source('category_management', 'range_review') }}
