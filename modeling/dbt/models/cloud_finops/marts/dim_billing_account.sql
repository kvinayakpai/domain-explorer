-- Billing-account dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_cloud_finops__hub_billing_account') }}),
     stg as (select * from {{ ref('stg_cloud_finops__billing_account') }})

select
    h.h_billing_account_hk      as billing_account_key,
    h.billing_account_bk        as billing_account_id,
    s.billing_account_name,
    s.provider,
    s.billing_currency,
    s.payer_account_id,
    s.subscription_tier,
    s.support_level,
    s.is_active,
    h.load_date                 as dim_loaded_at
from hub h
left join stg s on s.billing_account_id = h.billing_account_bk
