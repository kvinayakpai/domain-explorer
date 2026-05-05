-- Merchant dimension joined to MCC reference for category breakdowns.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_payments__hub_merchant') }}),
     stg as (select * from {{ ref('stg_payments__merchants') }}),
     mcc as (select * from {{ ref('stg_payments__mcc_codes') }})

select
    h.h_merchant_hk            as merchant_key,
    h.merchant_bk              as merchant_id,
    s.merchant_name,
    s.mcc,
    coalesce(m.mcc_description, s.merchant_description) as mcc_description,
    coalesce(m.mcc_category,    s.merchant_category)    as mcc_category,
    s.country_code,
    h.load_date                as dim_loaded_at
from hub h
left join stg s on s.merchant_id = h.merchant_bk
left join mcc m on m.mcc         = s.mcc
