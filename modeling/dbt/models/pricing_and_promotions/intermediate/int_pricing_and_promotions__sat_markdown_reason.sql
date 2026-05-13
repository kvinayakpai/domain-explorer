-- Vault satellite — Markdown event with reason and optimizer attribution.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_pricing_and_promotions__markdown') }})

select
    md5(markdown_id)                                                                          as h_markdown_hk,
    triggered_at                                                                              as load_ts,
    md5(cast(coalesce(pre_price_minor, 0) as varchar) || '|' || cast(coalesce(post_price_minor, 0) as varchar)
        || '|' || cast(coalesce(markdown_depth_pct, 0) as varchar)
        || '|' || coalesce(reason_code,'') || '|' || coalesce(optimizer,''))                  as hashdiff,
    pre_price_minor,
    post_price_minor,
    markdown_depth_pct,
    reason_code,
    optimizer,
    planned_sell_through_pct,
    actual_sell_through_pct,
    effective_from,
    effective_to,
    triggered_at,
    'pricing_and_promotions.markdown'                                                         as record_source
from src
