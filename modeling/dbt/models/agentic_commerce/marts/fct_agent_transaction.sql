{{ config(materialized='table') }}

with t as (select * from {{ ref('stg_agentic_commerce__agent_transactions') }}),
     a as (select * from {{ ref('dim_agent') }}),
     p as (select * from {{ ref('dim_principal') }}),
     m as (select * from {{ ref('dim_merchant_agentic') }}),
     s as (select * from {{ ref('dim_authorization_scope') }})

select
    t.agent_txn_id,
    cast(strftime(t.authorized_at, '%Y%m%d') as integer) as date_key,
    a.agent_sk,
    p.principal_sk,
    m.merchant_sk,
    s.scope_sk,
    t.cart_id,
    t.amount_minor,
    t.currency,
    -- Trivial USD normalization for the demo: USD pass-through, others approximated.
    case t.currency
        when 'USD' then t.amount_minor / 100.0
        when 'EUR' then t.amount_minor / 100.0 * 1.08
        when 'GBP' then t.amount_minor / 100.0 * 1.27
        when 'JPY' then t.amount_minor / 100.0 * 0.0067
        else t.amount_minor / 100.0
    end as amount_usd,
    t.stepup_method,
    t.is_stepup,
    case when t.status in ('authorized','captured','refunded','disputed') then true else false end as is_authorized,
    t.is_captured,
    t.is_declined,
    t.is_refunded,
    t.is_disputed,
    t.latency_ms,
    t.authorized_at,
    t.captured_at,
    t.psp,
    t.rail,
    t.scheme,
    t.agent_indicator
from t
left join a on a.agent_id     = t.agent_id
left join p on p.principal_id = t.principal_id
left join m on m.merchant_id  = t.merchant_id
left join s on s.grant_id     = t.grant_id
