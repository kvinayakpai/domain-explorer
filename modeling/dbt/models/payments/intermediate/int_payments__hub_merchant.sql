-- Vault-style hub for Merchant.
{{ config(materialized='ephemeral') }}

with src as (
    select merchant_id from {{ ref('stg_payments__merchants') }}
    where merchant_id is not null
    union
    select distinct merchant_id from {{ ref('stg_payments__payments') }}
    where merchant_id is not null
)

select
    md5(merchant_id) as h_merchant_hk,
    merchant_id      as merchant_bk,
    current_date     as load_date,
    'payments.merchants'   as record_source
from src
group by merchant_id
