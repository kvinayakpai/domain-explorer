-- Grain: one row per claim. Joins through Vault hubs/links to surface
-- policy + policyholder + adjuster keys, plus rolled-up payment / reserve
-- aggregates and FNOL channel signals.
{{ config(materialized='table') }}

with sat as (select * from {{ ref('int_p_and_c_claims__sat_claim') }}),
     hub_c as (select * from {{ ref('int_p_and_c_claims__hub_claim') }}),
     l_cp as (select * from {{ ref('int_p_and_c_claims__link_claim_policy') }}),
     stg_claim as (select * from {{ ref('stg_p_and_c_claims__claims') }}),
     pay_roll as (
         select
             cl.claim_id,
             count(p.payment_id)             as payment_count,
             coalesce(sum(p.amount), 0.0)    as paid_amount,
             max(p.paid_at)                  as last_paid_at
         from {{ ref('stg_p_and_c_claims__claim_lines') }} cl
         left join {{ ref('stg_p_and_c_claims__claim_payments') }} p
             on p.claim_line_id = cl.claim_line_id
         group by cl.claim_id
     ),
     reserve_roll as (
         select
             claim_id,
             coalesce(sum(reserve_amount), 0.0)  as reserve_amount,
             max(set_at)                         as last_reserve_set_at
         from {{ ref('stg_p_and_c_claims__reserves') }}
         group by claim_id
     ),
     fnol_roll as (
         select
             claim_id,
             min(received_at)                    as fnol_received_at,
             min(channel)                        as fnol_channel,
             coalesce(sum(duration_minutes), 0)  as fnol_total_minutes
         from {{ ref('stg_p_and_c_claims__fnol_events') }}
         group by claim_id
     )

select
    h.h_claim_hk                  as claim_key,
    h.claim_bk                    as claim_id,
    sc.policy_id,
    l_cp.h_policy_hk              as policy_key,
    md5(sc.adjuster_id)           as adjuster_key,
    sc.adjuster_id,
    cast(strftime(s.load_ts, '%Y%m%d') as integer) as fnol_date_key,
    s.fnol_ts,
    s.loss_date,
    s.report_lag_days,
    s.peril,
    s.severity,
    s.claim_status,
    s.incurred_amount,
    s.fraud_score,
    coalesce(pay_roll.paid_amount, 0.0)             as paid_amount,
    coalesce(pay_roll.payment_count, 0)             as payment_count,
    pay_roll.last_paid_at,
    coalesce(reserve_roll.reserve_amount, 0.0)      as reserve_amount,
    reserve_roll.last_reserve_set_at,
    fnol_roll.fnol_received_at,
    fnol_roll.fnol_channel,
    fnol_roll.fnol_total_minutes,
    case
        when s.incurred_amount > 0
            then coalesce(pay_roll.paid_amount, 0.0) / s.incurred_amount
    end                                              as paid_to_incurred_ratio
from hub_c h
join sat       s   on s.h_claim_hk  = h.h_claim_hk
left join l_cp     on l_cp.h_claim_hk = h.h_claim_hk
left join stg_claim sc on sc.claim_id = h.claim_bk
left join pay_roll     on pay_roll.claim_id      = h.claim_bk
left join reserve_roll on reserve_roll.claim_id  = h.claim_bk
left join fnol_roll    on fnol_roll.claim_id     = h.claim_bk
