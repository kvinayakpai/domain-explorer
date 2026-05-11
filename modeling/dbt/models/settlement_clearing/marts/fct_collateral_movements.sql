-- Grain: one row per collateral movement.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_settlement_clearing__collateral_movement') }}),
     pg as (select * from {{ ref('dim_party_settlement_clearing') }}),
     pt as (select * from {{ ref('dim_party_settlement_clearing') }})

select
    md5(c.collateral_movement_id)                            as collateral_movement_key,
    c.collateral_movement_id,
    c.collateral_giver_party_id,
    pg.party_key                                             as giver_party_key,
    c.collateral_taker_party_id,
    pt.party_key                                             as taker_party_key,
    c.direction,
    c.collateral_type,
    c.quantity,
    c.market_value,
    c.haircut_pct,
    c.post_haircut_value,
    c.currency,
    cast({{ format_date('c.movement_ts', '%Y%m%d') }} as integer)        as movement_date_key,
    c.movement_ts,
    c.status
from c
left join pg on pg.party_id = c.collateral_giver_party_id
left join pt on pt.party_id = c.collateral_taker_party_id
