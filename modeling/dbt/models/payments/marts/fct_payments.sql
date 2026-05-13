-- Grain: one row per payment event. Joins through Vault hubs/links to surface
-- foreign keys for both customer and merchant dims.
{{ config(materialized='table') }}

with sat as (select * from {{ ref('int_payments__sat_payment') }}),
     hub_p as (select * from {{ ref('int_payments__hub_payment') }}),
     l_pc as (select * from {{ ref('int_payments__link_payment_customer') }}),
     l_pm as (select * from {{ ref('int_payments__link_payment_merchant') }}),
     fa as (
         select payment_id, max(score) as fraud_score, count(*) as fraud_alert_count
         from {{ ref('stg_payments__fraud_alerts') }}
         group by payment_id
     )

select
    h.h_payment_hk              as payment_key,
    h.payment_bk                as payment_id,
    cast({{ format_date('s.load_ts', '%Y%m%d') }} as integer) as auth_date_key,
    s.load_ts                   as auth_ts,
    s.settlement_ts,
    s.settlement_latency_hours,
    s.rail,
    s.auth_status,
    s.is_stp,
    s.amount,
    s.currency,
    s.interchange_amount,
    s.country_code,
    l_pc.h_customer_hk          as customer_key,
    l_pm.h_merchant_hk          as merchant_key,
    coalesce(fa.fraud_alert_count, 0) as fraud_alert_count,
    fa.fraud_score              as max_fraud_score
from hub_p h
join sat   s    on s.h_payment_hk  = h.h_payment_hk
left join l_pc  on l_pc.h_payment_hk = h.h_payment_hk
left join l_pm  on l_pm.h_payment_hk = h.h_payment_hk
left join fa    on fa.payment_id     = h.payment_bk
