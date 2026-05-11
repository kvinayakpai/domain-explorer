-- Grain: one row per execution (FIX fill).
{{ config(materialized='table') }}

with e as (select * from {{ ref('stg_capital_markets__execution') }}),
     o as (select order_id, account_id, submitting_party_id from {{ ref('stg_capital_markets__order') }}),
     i as (select * from {{ ref('dim_instrument_capital_markets') }}),
     a as (select * from {{ ref('dim_account_capital_markets') }}),
     v as (select * from {{ ref('dim_venue_capital_markets') }})

select
    md5(e.execution_id)                                  as execution_key,
    e.execution_id,
    e.exec_id,
    e.order_id,
    e.exec_type,
    e.ord_status,
    e.side,
    e.last_qty,
    e.last_px,
    e.last_qty * e.last_px                               as notional,
    e.commission,
    e.liquidity_indicator,
    cast({{ format_date('e.exec_ts', '%Y%m%d') }} as integer)        as exec_date_key,
    e.exec_ts,
    i.instrument_key,
    a.account_key,
    v.venue_key,
    o.submitting_party_id
from e
left join o on o.order_id      = e.order_id
left join i on i.instrument_id = e.instrument_id
left join a on a.account_id    = o.account_id
left join v on v.mic           = e.venue_mic
