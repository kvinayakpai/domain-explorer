-- Grain: one row per trade allocation.
{{ config(materialized='table') }}

with al as (select * from {{ ref('stg_capital_markets__allocation') }}),
     t  as (select trade_id, instrument_id from {{ ref('stg_capital_markets__trade') }}),
     a  as (select * from {{ ref('dim_account_capital_markets') }}),
     i  as (select * from {{ ref('dim_instrument_capital_markets') }})

select
    md5(al.allocation_id)         as allocation_key,
    al.allocation_id,
    al.trade_id,
    md5(al.trade_id)              as trade_key,
    a.account_key                 as client_account_key,
    i.instrument_key,
    al.allocated_qty,
    al.allocated_amount,
    al.average_price,
    al.status
from al
left join t  on t.trade_id        = al.trade_id
left join a  on a.account_id      = al.client_account_id
left join i  on i.instrument_id   = t.instrument_id
