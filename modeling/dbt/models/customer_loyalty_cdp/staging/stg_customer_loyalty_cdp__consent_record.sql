{{ config(materialized='view') }}

select
    cast(consent_id        as varchar)    as consent_id,
    cast(customer_id       as varchar)    as customer_id,
    cast(jurisdiction      as varchar)    as jurisdiction,
    cast(consent_basis     as varchar)    as consent_basis,
    cast(consent_string    as varchar)    as consent_string,
    cast(purpose_codes     as varchar)    as purpose_codes,
    cast(action            as varchar)    as action,
    cast(source_system     as varchar)    as source_system,
    cast(event_ts          as timestamp)  as event_ts,
    cast(ip_token          as varchar)    as ip_token,
    cast(user_agent_token  as varchar)    as user_agent_token
from {{ source('customer_loyalty_cdp', 'consent_record') }}
