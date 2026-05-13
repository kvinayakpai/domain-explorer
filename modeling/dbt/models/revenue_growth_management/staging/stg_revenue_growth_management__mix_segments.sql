{{ config(materialized='view') }}

select
    cast(segment_id                          as varchar) as segment_id,
    cast(channel                             as varchar) as channel,
    cast(ppa_tier                            as varchar) as ppa_tier,
    cast(category                            as varchar) as category,
    cast(target_share_pct                    as double)  as target_share_pct,
    cast(target_net_revenue_per_unit_cents   as bigint)  as target_net_revenue_per_unit_cents
from {{ source('revenue_growth_management', 'mix_segment') }}
