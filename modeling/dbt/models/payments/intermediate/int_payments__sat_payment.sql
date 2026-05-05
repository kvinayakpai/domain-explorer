-- Vault-style satellite carrying descriptive Payment attributes.
-- Hashdiff lets downstream models detect attribute changes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_payments__payments') }}
)

select
    md5(payment_id)                                     as h_payment_hk,
    auth_ts                                             as load_ts,
    md5(coalesce(rail,'') || '|' || coalesce(auth_status,'') || '|'
        || coalesce(currency,'') || '|' || cast(amount as varchar))
                                                        as hashdiff,
    rail,
    auth_status,
    is_stp,
    amount,
    currency,
    interchange_amount,
    settlement_ts,
    settlement_latency_hours,
    country_code,
    'payments.payments'                                 as record_source
from src
