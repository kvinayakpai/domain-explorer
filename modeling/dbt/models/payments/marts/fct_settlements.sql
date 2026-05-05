-- Grain: one row per settlement record.
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_payments__settlements') }}),
     hub_p as (select * from {{ ref('int_payments__hub_payment') }})

select
    md5(s.settlement_id)                   as settlement_key,
    s.settlement_id,
    h.h_payment_hk                         as payment_key,
    s.payment_id,
    s.batch_id,
    s.network,
    cast(strftime(s.settled_at, '%Y%m%d') as integer) as settled_date_key,
    s.settled_at,
    s.amount,
    s.currency,
    s.fee_amount,
    s.fee_amount / nullif(s.amount, 0)    as fee_rate
from stg s
left join hub_p h on h.payment_bk = s.payment_id
