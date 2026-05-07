-- Policy dimension joined to the policyholder hub.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_p_and_c_claims__hub_policy') }}),
     stg as (select * from {{ ref('stg_p_and_c_claims__policies') }}),
     l   as (select * from {{ ref('int_p_and_c_claims__link_policy_policyholder') }})

select
    h.h_policy_hk                as policy_key,
    h.policy_bk                  as policy_id,
    s.policyholder_id,
    l.h_policyholder_hk          as policyholder_key,
    s.line_of_business,
    s.carrier,
    s.premium_annual,
    s.deductible,
    s.effective_date,
    s.expires_date,
    s.policy_state,
    cast(date_diff('day', s.effective_date, s.expires_date) as integer) as policy_duration_days,
    h.load_date                  as dim_loaded_at
from hub h
left join stg s on s.policy_id    = h.policy_bk
left join l    on l.h_policy_hk   = h.h_policy_hk
