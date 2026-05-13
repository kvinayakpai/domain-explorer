-- Tactic dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_trade_promotion_management__hub_tactic') }}),
     stg as (select * from {{ ref('stg_trade_promotion_management__promo_tactic') }})

select
    h.h_tactic_hk             as tactic_sk,
    h.tactic_bk               as tactic_id,
    s.promotion_id,
    s.sku_id,
    s.tactic_type,
    s.discount_per_unit_cents,
    s.consumer_price_cents,
    s.srp_cents,
    s.feature_type,
    s.display_type,
    s.tpr_only,
    s.settlement_method
from hub h
left join stg s on s.tactic_id = h.tactic_bk
