-- Promotion dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_trade_promotion_management__hub_promotion') }}),
     stg as (select * from {{ ref('stg_trade_promotion_management__promotion') }})

select
    h.h_promotion_hk        as promotion_sk,
    h.promotion_bk          as promotion_id,
    s.account_id,
    s.name,
    s.fiscal_year,
    s.fiscal_quarter,
    s.start_date,
    s.end_date,
    s.ship_start_date,
    s.ship_end_date,
    s.status,
    s.planned_spend_cents,
    s.planned_volume_units,
    s.planned_lift_pct,
    s.forecast_roi,
    s.created_by,
    s.created_at,
    s.approved_at
from hub h
left join stg s on s.promotion_id = h.promotion_bk
