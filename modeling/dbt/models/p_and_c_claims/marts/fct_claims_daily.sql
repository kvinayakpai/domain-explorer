-- Grain: one row per (FNOL date, peril). Useful for trend dashboards
-- showing claim volume / incurred / paid by reporting day and peril.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_p_and_c_claims__claims') }}),
     pay_per_claim as (
         select
             cl.claim_id,
             coalesce(sum(p.amount), 0.0) as paid_amount
         from {{ ref('stg_p_and_c_claims__claim_lines') }} cl
         left join {{ ref('stg_p_and_c_claims__claim_payments') }} p
             on p.claim_line_id = cl.claim_line_id
         group by cl.claim_id
     ),
     reserve_per_claim as (
         select claim_id, coalesce(sum(reserve_amount), 0.0) as reserve_amount
         from {{ ref('stg_p_and_c_claims__reserves') }}
         group by claim_id
     ),
     agg as (
         select
             cast({{ format_date('c.fnol_ts', '%Y%m%d') }} as integer)    as fnol_date_key,
             cast(c.fnol_ts as date)                            as fnol_date,
             c.peril                                            as peril,
             count(*)                                           as claim_count,
             sum(case when c.claim_status = 'OPEN'      then 1 else 0 end) as open_claim_count,
             sum(case when c.claim_status = 'CLOSED'    then 1 else 0 end) as closed_claim_count,
             sum(case when c.claim_status = 'WITHDRAWN' then 1 else 0 end) as withdrawn_claim_count,
             sum(case when c.claim_status = 'DENIED'    then 1 else 0 end) as denied_claim_count,
             coalesce(sum(c.incurred_amount), 0.0)              as total_incurred_amount,
             coalesce(sum(pay_per_claim.paid_amount), 0.0)      as total_paid_amount,
             coalesce(sum(reserve_per_claim.reserve_amount),0.0)as total_reserve_amount,
             avg(c.report_lag_days)                              as avg_report_lag_days,
             avg(c.fraud_score)                                  as avg_fraud_score
         from c
         left join pay_per_claim     on pay_per_claim.claim_id     = c.claim_id
         left join reserve_per_claim on reserve_per_claim.claim_id = c.claim_id
         group by 1, 2, 3
     )

select
    md5(cast(fnol_date_key as varchar) || '|' || coalesce(peril,'unknown')) as claims_daily_key,
    fnol_date_key,
    fnol_date,
    peril,
    claim_count,
    open_claim_count,
    closed_claim_count,
    withdrawn_claim_count,
    denied_claim_count,
    total_incurred_amount,
    total_paid_amount,
    total_reserve_amount,
    avg_report_lag_days,
    avg_fraud_score
from agg
