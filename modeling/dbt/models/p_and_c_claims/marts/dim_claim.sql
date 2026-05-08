-- Claim dimension: one row per claim header with descriptive attributes only.
-- Numeric / payment / reserve facts live in fct_claims and fct_claims_daily.
{{ config(materialized='table') }}

with hub_c as (select * from {{ ref('int_p_and_c_claims__hub_claim') }}),
     sat   as (select * from {{ ref('int_p_and_c_claims__sat_claim') }}),
     stg   as (select * from {{ ref('stg_p_and_c_claims__claims') }})

select
    h.h_claim_hk                                        as claim_key,
    h.claim_bk                                          as claim_id,
    stg.policy_id,
    stg.adjuster_id,
    md5(stg.adjuster_id)                                as adjuster_key,
    stg.peril,
    stg.severity,
    stg.claim_status,
    case
        when stg.claim_status in ('CLOSED', 'WITHDRAWN', 'DENIED') then false
        else true
    end                                                 as is_open,
    stg.fnol_ts,
    stg.loss_date,
    stg.report_lag_days,
    case
        when stg.report_lag_days is null               then 'unknown'
        when stg.report_lag_days <= 1                  then 'same_day'
        when stg.report_lag_days <= 7                  then 'within_week'
        when stg.report_lag_days <= 30                 then 'within_month'
        else 'late'
    end                                                 as report_lag_band,
    cast(strftime(stg.fnol_ts, '%Y%m%d') as integer)    as fnol_date_key,
    cast(strftime(stg.loss_date, '%Y%m%d') as integer)  as loss_date_key,
    s.fraud_score,
    case
        when s.fraud_score is null   then 'unknown'
        when s.fraud_score >= 0.75   then 'high'
        when s.fraud_score >= 0.40   then 'medium'
        else 'low'
    end                                                 as fraud_risk_band
from hub_c h
join sat s   on s.h_claim_hk = h.h_claim_hk
left join stg on stg.claim_id = h.claim_bk
