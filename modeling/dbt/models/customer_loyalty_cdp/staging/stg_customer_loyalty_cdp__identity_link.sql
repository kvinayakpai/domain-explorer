{{ config(materialized='view') }}

select
    cast(identity_id            as varchar)    as identity_id,
    cast(customer_id            as varchar)    as customer_id,
    cast(identifier_type        as varchar)    as identifier_type,
    cast(identifier_value_hash  as varchar)    as identifier_value_hash,
    cast(match_method           as varchar)    as match_method,
    cast(match_confidence       as double)     as match_confidence,
    cast(source_system          as varchar)    as source_system,
    cast(first_observed_at      as timestamp)  as first_observed_at,
    cast(last_observed_at       as timestamp)  as last_observed_at,
    cast(is_active              as boolean)    as is_active
from {{ source('customer_loyalty_cdp', 'identity_link') }}
