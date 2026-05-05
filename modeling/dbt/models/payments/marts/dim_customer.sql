-- Customer dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_payments__hub_customer') }}),
     stg as (select * from {{ ref('stg_payments__customers') }})

select
    h.h_customer_hk           as customer_key,
    h.customer_bk             as customer_id,
    s.full_name,
    s.email,
    s.country_code,
    s.kyc_status,
    s.risk_segment,
    s.signup_date,
    cast(date_diff('day', s.signup_date, current_date) / 365.25 as integer)
                              as tenure_years,
    h.load_date               as dim_loaded_at
from hub h
left join stg s on s.customer_id = h.customer_bk
