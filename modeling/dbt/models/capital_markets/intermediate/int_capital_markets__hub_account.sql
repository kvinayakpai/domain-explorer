-- Vault hub for the Account business key.
{{ config(materialized='ephemeral') }}

with src as (
    select account_id
    from {{ ref('stg_capital_markets__account') }}
    where account_id is not null
)

select
    md5(account_id)                as h_account_hk,
    account_id                     as account_bk,
    current_date                   as load_date,
    'capital_markets.account'      as record_source
from src
group by account_id
