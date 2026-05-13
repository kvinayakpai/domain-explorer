{{ config(materialized='table') }}

select
    row_number() over (order by segment_id) as segment_sk,
    segment_id,
    channel,
    ppa_tier,
    category,
    target_share_pct,
    target_net_revenue_per_unit_cents
from {{ ref('stg_revenue_growth_management__mix_segments') }}
