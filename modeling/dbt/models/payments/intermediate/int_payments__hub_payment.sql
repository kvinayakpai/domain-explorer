-- Vault-style hub for Payment.
{{ config(materialized='ephemeral') }}

with src as (
    select payment_id, auth_ts
    from {{ ref('stg_payments__payments') }}
    where payment_id is not null
)

select
    md5(payment_id)             as h_payment_hk,
    payment_id                  as payment_bk,
    min(auth_ts)                as load_ts,
    'payments.payments'         as record_source
from src
group by payment_id
