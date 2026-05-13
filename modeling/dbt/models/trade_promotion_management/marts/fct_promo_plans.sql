-- Fact: one row per planned tactic, with plan-vs-actual columns and FKs to
--       dim_promotion / dim_tactic / dim_account_tpm / dim_product_tpm.
{{ config(materialized='table') }}

with t as (select * from {{ ref('stg_trade_promotion_management__promo_tactic') }}),
     p as (select * from {{ ref('stg_trade_promotion_management__promotion') }}),
     dp as (select * from {{ ref('dim_promotion') }}),
     dt as (select * from {{ ref('dim_tactic') }}),
     da as (select * from {{ ref('dim_account_tpm') }}),
     dpr as (select * from {{ ref('dim_product_tpm') }})

select
    t.tactic_id                                                      as plan_event_id,
    dp.promotion_sk,
    dt.tactic_sk,
    da.account_sk,
    dpr.product_sk,
    cast({{ format_date('p.created_at', '%Y%m%d') }} as integer)     as plan_date_key,
    cast({{ format_date('p.start_date', '%Y%m%d') }} as integer)     as start_date_key,
    cast({{ format_date('p.end_date', '%Y%m%d') }}   as integer)     as end_date_key,
    t.planned_units,
    t.planned_spend_cents,
    p.planned_lift_pct,
    p.forecast_roi,
    cast(1 as smallint)                                              as plan_version
from t
left join p   on p.promotion_id = t.promotion_id
left join dp  on dp.promotion_id = t.promotion_id
left join dt  on dt.tactic_id    = t.tactic_id
left join da  on da.account_id   = p.account_id
left join dpr on dpr.sku_id      = t.sku_id
