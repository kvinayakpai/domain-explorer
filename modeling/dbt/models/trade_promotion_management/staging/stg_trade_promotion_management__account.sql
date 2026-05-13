{{ config(materialized='view') }}

select
    cast(account_id        as varchar)   as account_id,
    cast(account_name      as varchar)   as account_name,
    cast(parent_account_id as varchar)   as parent_account_id,
    cast(channel           as varchar)   as channel,
    cast(country_iso2      as varchar)   as country_iso2,
    cast(gln               as varchar)   as gln,
    cast(trade_terms_code  as varchar)   as trade_terms_code,
    cast(status            as varchar)   as status,
    cast(created_at        as timestamp) as created_at
from {{ source('trade_promotion_management', 'account') }}
