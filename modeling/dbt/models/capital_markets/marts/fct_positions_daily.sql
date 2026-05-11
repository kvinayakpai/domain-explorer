-- Grain: account x instrument x as_of_date.
{{ config(materialized='table') }}

with p as (select * from {{ ref('stg_capital_markets__position') }}),
     i as (select * from {{ ref('dim_instrument_capital_markets') }}),
     a as (select * from {{ ref('dim_account_capital_markets') }})

select
    md5(p.position_id)                                       as position_key,
    p.position_id,
    cast({{ format_date('p.as_of_date', '%Y%m%d') }} as integer)        as position_date_key,
    p.as_of_date,
    a.account_key,
    i.instrument_key,
    p.quantity,
    case when p.quantity > 0 then p.quantity else 0 end      as long_qty,
    case when p.quantity < 0 then -p.quantity else 0 end     as short_qty,
    p.quantity                                                as net_qty,
    p.average_price,
    p.market_value,
    p.currency
from p
left join i on i.instrument_id = p.instrument_id
left join a on a.account_id    = p.account_id
