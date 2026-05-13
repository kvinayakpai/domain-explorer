{{ config(materialized='view') }}

select
    cast(preference_id    as varchar)    as preference_id,
    cast(customer_id      as varchar)    as customer_id,
    cast(channel          as varchar)    as channel,
    cast(topic            as varchar)    as topic,
    cast(state            as varchar)    as state,
    cast(source_system    as varchar)    as source_system,
    cast(changed_at       as timestamp)  as changed_at,
    cast(effective_until  as timestamp)  as effective_until
from {{ source('customer_loyalty_cdp', 'preference_center') }}
