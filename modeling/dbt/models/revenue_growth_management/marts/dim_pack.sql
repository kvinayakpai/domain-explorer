{{ config(materialized='table') }}

select
    row_number() over (order by pack_id) as pack_sk,
    pack_id,
    sku_id,
    pack_name,
    pack_size_count,
    pack_format,
    ppa_tier,
    ladder_rank,
    benchmark_net_price_cents,
    benchmark_margin_cents,
    status
from {{ ref('stg_revenue_growth_management__packs') }}
