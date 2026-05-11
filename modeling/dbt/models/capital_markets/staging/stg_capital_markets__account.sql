-- Staging: trading account.
{{ config(materialized='view') }}

select
    cast(account_id     as varchar) as account_id,
    cast(owner_party_id as varchar) as owner_party_id,
    cast(account_type   as varchar) as account_type,
    upper(currency)                 as base_currency,
    cast(status         as varchar) as status
from {{ source('capital_markets', 'account') }}
