-- Grain: one row per indemnity payment. Brief-aligned alias of fct_claim_payments
-- with policy and peril context surfaced for slicing.
{{ config(materialized='table') }}

with p as (select * from {{ ref('stg_p_and_c_claims__claim_payments') }}),
     l as (select * from {{ ref('stg_p_and_c_claims__claim_lines') }}),
     hub_c as (select * from {{ ref('int_p_and_c_claims__hub_claim') }}),
     stg_claim as (select * from {{ ref('stg_p_and_c_claims__claims') }})

select
    md5(p.payment_id)                                   as payment_key,
    p.payment_id,
    p.claim_line_id,
    l.claim_id,
    h.h_claim_hk                                        as claim_key,
    stg_claim.policy_id,
    stg_claim.peril,
    stg_claim.severity,
    l.coverage,
    l.amount                                            as line_amount,
    p.amount                                            as paid_amount,
    p.payment_method,
    p.paid_at,
    cast(strftime(p.paid_at, '%Y%m%d') as integer)      as paid_date_key,
    case
        when l.amount > 0 then p.amount / l.amount
    end                                                 as line_paid_ratio,
    case when p.amount > 1000000 then true else false end as is_large_payment
from p
left join l         on l.claim_line_id = p.claim_line_id
left join hub_c h   on h.claim_bk     = l.claim_id
left join stg_claim on stg_claim.claim_id = l.claim_id
