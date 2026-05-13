-- Policyholder dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_p_and_c_claims__hub_policyholder') }}),
     stg as (select * from {{ ref('stg_p_and_c_claims__policyholders') }})

select
    h.h_policyholder_hk          as policyholder_key,
    h.policyholder_bk            as policyholder_id,
    s.full_name,
    s.email,
    s.country_code,
    s.credit_band,
    s.tenure_years,
    h.load_date                  as dim_loaded_at
from hub h
left join stg s on s.policyholder_id = h.policyholder_bk
