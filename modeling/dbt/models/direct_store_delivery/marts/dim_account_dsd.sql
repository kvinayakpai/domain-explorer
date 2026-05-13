-- Account dimension (DSD-suffixed; trade_promotion_management publishes
-- dim_account_tpm at the same level — the two are conformable but not identical).
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_direct_store_delivery__account') }})

select
    md5(account_id)                  as account_sk,
    account_id,
    account_name,
    channel,
    country_iso2,
    trade_terms_code,
    status
from stg
