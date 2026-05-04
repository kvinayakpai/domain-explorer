-- Staging model: lightly typed, renamed view of payments_raw.authorizations.
{{ config(materialized='view') }}

select
    cast(auth_id as varchar)        as auth_id,
    cast(transaction_id as varchar) as transaction_id,
    cast(merchant_id as varchar)    as merchant_id,
    cast(amount_minor as bigint)    as amount_minor,
    upper(currency)                 as currency,
    cast(approved as boolean)       as approved,
    cast(auth_ts as timestamp)      as auth_ts
from {{ source('payments_raw', 'authorizations') }}
