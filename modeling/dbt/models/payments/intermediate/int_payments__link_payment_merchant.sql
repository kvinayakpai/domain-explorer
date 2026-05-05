-- Vault-style link between Payment and Merchant.
{{ config(materialized='ephemeral') }}

with src as (
    select payment_id, merchant_id
    from {{ ref('stg_payments__payments') }}
    where payment_id is not null and merchant_id is not null
)

select
    md5(payment_id || '|' || merchant_id) as l_payment_merchant_hk,
    md5(payment_id)                       as h_payment_hk,
    md5(merchant_id)                      as h_merchant_hk,
    current_date                          as load_date,
    'payments.payments'                   as record_source
from src
group by payment_id, merchant_id
