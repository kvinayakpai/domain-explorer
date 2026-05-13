{{ config(materialized='table') }}

-- Mix analysis fact — variance decomposition (volume / price / mix) per
-- channel × tier × category segment × week. The dashboard reads this directly.
with s as (
    select
        s.account_id,
        s.pack_id,
        s.units,
        s.net_revenue_cents,
        s.gross_revenue_cents,
        s.invoice_date,
        a.channel,
        a.channel_tier,
        p.ppa_tier,
        p.benchmark_net_price_cents,
        prod.category
    from {{ ref('stg_revenue_growth_management__sales_transactions') }} s
    left join {{ ref('stg_revenue_growth_management__accounts') }} a   on a.account_id = s.account_id
    left join {{ ref('stg_revenue_growth_management__packs') }}    p   on p.pack_id    = s.pack_id
    left join {{ ref('stg_revenue_growth_management__products') }} prod on prod.sku_id = p.sku_id
),
agg as (
    select
        channel,
        ppa_tier,
        category,
        date_trunc('month', invoice_date)              as period,
        sum(units)                                     as actual_units,
        sum(net_revenue_cents)                         as actual_net_revenue_cents,
        sum(units * benchmark_net_price_cents)         as plan_net_revenue_cents,
        sum(units)                                     as plan_units    -- placeholder; plan grain not yet materialized
    from s
    where channel is not null
      and ppa_tier is not null
      and category is not null
    group by 1, 2, 3, 4
),
seg as (
    select * from {{ ref('dim_mix_segment') }}
),
joined as (
    select
        agg.*,
        seg.segment_sk
    from agg
    left join seg
      on seg.channel  = agg.channel
     and seg.ppa_tier = agg.ppa_tier
     and seg.category = agg.category
),
totals as (
    select
        period,
        sum(actual_units)            as total_actual_units,
        sum(plan_units)              as total_plan_units,
        sum(actual_net_revenue_cents) as total_actual_nr,
        sum(plan_net_revenue_cents)   as total_plan_nr
    from joined
    group by 1
)
select
    cast({{ dbt_utils.generate_surrogate_key(['joined.channel','joined.ppa_tier','joined.category','joined.period']) }} as varchar) as mix_row_id,
    cast({{ format_date('cast(joined.period as date)', '%Y%m%d') }} as integer) as date_key,
    joined.segment_sk,
    cast(null as bigint)                                                       as account_sk,
    cast(null as bigint)                                                       as pack_sk,
    joined.actual_units,
    joined.plan_units,
    case when totals.total_actual_units > 0
         then cast(joined.actual_units as double) / totals.total_actual_units
    end as actual_share_pct,
    case when totals.total_plan_units > 0
         then cast(joined.plan_units as double) / totals.total_plan_units
    end as plan_share_pct,
    joined.actual_net_revenue_cents,
    joined.plan_net_revenue_cents,
    cast(joined.actual_units - joined.plan_units as bigint)                    as volume_variance_cents,
    cast(joined.actual_net_revenue_cents - joined.plan_net_revenue_cents - (joined.actual_units - joined.plan_units) as bigint)
                                                                                as price_variance_cents,
    cast(0 as bigint)                                                          as mix_variance_cents,
    cast(0 as bigint)                                                          as residual_variance_cents
from joined
join totals on totals.period = joined.period
