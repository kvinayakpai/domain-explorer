-- Grain: one row per chargeback. Optionally joined to its dispute follow-up.
{{ config(materialized='table') }}

with cb as (select * from {{ ref('stg_payments__chargebacks') }}),
     dp as (
         select
             chargeback_id,
             min(opened_ts)             as first_opened_ts,
             max(resolved_ts)           as last_resolved_ts,
             max(resolution_days)       as max_resolution_days,
             count(*)                   as dispute_count
         from {{ ref('stg_payments__disputes') }}
         group by chargeback_id
     ),
     hub_p as (select * from {{ ref('int_payments__hub_payment') }})

select
    md5(cb.chargeback_id)                          as chargeback_key,
    cb.chargeback_id,
    h.h_payment_hk                                 as payment_key,
    cb.payment_id,
    cb.reason_code,
    cb.amount,
    cb.status                                      as chargeback_status,
    cast({{ format_date('cb.filed_at', '%Y%m%d') }} as integer) as filed_date_key,
    cb.filed_at,
    coalesce(dp.dispute_count, 0)                  as dispute_count,
    dp.first_opened_ts                             as dispute_opened_ts,
    dp.last_resolved_ts                            as dispute_resolved_ts,
    dp.max_resolution_days                         as resolution_days
from cb
left join hub_p h on h.payment_bk = cb.payment_id
left join dp     on dp.chargeback_id = cb.chargeback_id
