-- Fact: weekly post-event performance per tactic.
-- Suffix `_tpm` avoids collision with pricing_and_promotions.fct_promo_performance.
{{ config(materialized='table') }}

with l as (select * from {{ ref('stg_trade_promotion_management__lift_observation') }}),
     t as (select * from {{ ref('stg_trade_promotion_management__promo_tactic') }}),
     dt as (select * from {{ ref('dim_tactic') }}),
     dp as (select * from {{ ref('dim_promotion') }}),
     da as (select * from {{ ref('dim_account_tpm') }}),
     dpr as (select * from {{ ref('dim_product_tpm') }})

select
    l.lift_observation_id                                                   as perf_id,
    dt.tactic_sk,
    dp.promotion_sk,
    da.account_sk,
    dpr.product_sk,
    cast({{ format_date('l.week_start_date', '%Y%m%d') }} as integer)       as week_date_key,
    l.actual_units,
    l.baseline_units,
    l.incremental_units,
    l.lift_pct,
    l.cannibalization_units,
    l.halo_units,
    t.actual_spend_cents,
    l.incremental_gross_profit_cents,
    l.actual_roi,
    l.source
from l
left join t   on t.tactic_id    = l.tactic_id
left join dt  on dt.tactic_id   = l.tactic_id
left join dp  on dp.promotion_id = t.promotion_id
left join da  on da.account_id  = l.account_id
left join dpr on dpr.sku_id     = l.sku_id
