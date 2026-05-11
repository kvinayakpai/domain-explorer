-- Vault-style hub for the Transaction business key.
{{ config(materialized='ephemeral') }}

with src as (
    select transaction_id, started_at
    from {{ ref('stg_ev_charging__transaction') }}
    where transaction_id is not null
)

select
    md5(transaction_id)                   as h_transaction_hk,
    transaction_id                        as transaction_bk,
    min(started_at)                       as load_ts,
    'ev_charging.transaction'             as record_source
from src
group by transaction_id
