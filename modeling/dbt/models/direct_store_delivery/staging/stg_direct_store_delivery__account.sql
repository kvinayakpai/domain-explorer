{{ config(materialized='view') }}

select
    cast(account_id       as varchar) as account_id,
    cast(account_name     as varchar) as account_name,
    cast(channel          as varchar) as channel,
    cast(country_iso2     as varchar) as country_iso2,
    cast(trade_terms_code as varchar) as trade_terms_code,
    cast(status           as varchar) as status
from {{ source('direct_store_delivery', 'account') }}
