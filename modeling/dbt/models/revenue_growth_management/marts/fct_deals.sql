{{ config(materialized='table') }}

with d  as (select * from {{ ref('stg_revenue_growth_management__deals') }}),
     a  as (select * from {{ ref('dim_account_rgm') }}),
     p  as (select * from {{ ref('dim_pack') }}),
     -- crude baseline-per-deal approximation: average of the pack-account baseline
     b  as (
        select account_id, pack_id, sum(baseline_units) as baseline_units_sum, count(*) as wk_cnt
        from {{ ref('stg_revenue_growth_management__baselines') }}
        group by 1,2
     )

select
    d.deal_id,
    cast({{ format_date('cast(d.start_date as date)', '%Y%m%d') }} as integer) as date_key,
    a.account_sk,
    p.pack_sk,
    d.promo_plan_id,
    d.tactic_type,
    d.mechanic,
    d.discount_per_unit_cents,
    d.rebate_pct,
    d.deal_floor_cents,
    d.planned_units,
    d.planned_spend_cents,
    d.actual_units,
    d.actual_spend_cents,
    d.forward_buy_cost_cents,
    -- Incremental units & revenue against baseline if joinable.
    cast(coalesce(d.actual_units - coalesce(b.baseline_units_sum, 0), 0) as bigint) as incremental_units,
    cast(coalesce((d.actual_units - coalesce(b.baseline_units_sum, 0)) * d.discount_per_unit_cents, 0) as bigint) as incremental_revenue_cents,
    case
        when d.actual_spend_cents > 0
            then cast((d.actual_units - coalesce(b.baseline_units_sum, 0)) * d.discount_per_unit_cents as double) / d.actual_spend_cents
    end as roi,
    d.start_date,
    d.end_date,
    d.settlement_method,
    d.status
from d
left join a on a.account_id = d.account_id
left join p on p.pack_id    = d.pack_id
left join b on b.account_id = d.account_id and b.pack_id = d.pack_id
