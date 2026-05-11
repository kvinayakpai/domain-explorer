-- Grain: one row per booked trade.
{{ config(materialized='table') }}

with t as (select * from {{ ref('stg_capital_markets__trade') }}),
     l as (select * from {{ ref('int_capital_markets__link_trade_components') }}),
     i as (select * from {{ ref('dim_instrument_capital_markets') }}),
     a as (select * from {{ ref('dim_account_capital_markets') }}),
     p as (select * from {{ ref('dim_party_capital_markets') }}),
     v as (select * from {{ ref('dim_venue_capital_markets') }})

select
    md5(t.trade_id)                                      as trade_key,
    t.trade_id,
    t.execution_id,
    t.side,
    t.quantity,
    t.price,
    t.gross_amount,
    t.currency,
    cast({{ format_date('t.trade_date', '%Y%m%d') }} as integer)      as trade_date_key,
    cast({{ format_date('t.settlement_date', '%Y%m%d') }} as integer) as settlement_date_key,
    i.instrument_key,
    a.account_key,
    p.party_key                                          as submitting_party_key,
    v.venue_key
from t
left join l on l.h_trade_hk    = md5(t.trade_id)
left join i on i.instrument_id = t.instrument_id
left join a on a.account_id    = t.account_id
left join p on md5(p.party_id) = l.h_party_hk
left join v on v.mic           = t.venue_mic
