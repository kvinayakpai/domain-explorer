{{ config(materialized='view') }}

select
    cast(price_list_id    as varchar)   as price_list_id,
    cast(account_id       as varchar)   as account_id,
    cast(pack_id          as varchar)   as pack_id,
    cast(list_price_cents as bigint)    as list_price_cents,
    cast(srp_cents        as bigint)    as srp_cents,
    upper(currency)                      as currency,
    cast(effective_from   as date)      as effective_from,
    cast(effective_to     as date)      as effective_to,
    cast(recorded_at      as timestamp) as recorded_at,
    cast(source_system    as varchar)   as source_system,
    cast(status           as varchar)   as status
from {{ source('revenue_growth_management', 'price_list') }}
