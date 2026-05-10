{{ config(materialized='view') }}

select
    cast(intent_id          as varchar)    as intent_id,
    cast(session_id         as varchar)    as session_id,
    cast(principal_id       as varchar)    as principal_id,
    cast(agent_id           as varchar)    as agent_id,
    cast(intent_text_hash   as varchar)    as intent_text_hash,
    cast(category_hint      as varchar)    as category_hint,
    cast(budget_min_minor   as bigint)     as budget_min_minor,
    cast(budget_max_minor   as bigint)     as budget_max_minor,
    upper(budget_currency)                  as budget_currency,
    cast(deadline_ts        as timestamp)  as deadline_ts,
    cast(state              as varchar)    as state,
    cast(created_at         as timestamp)  as created_at,
    cast(resolved_at        as timestamp)  as resolved_at,
    case
        when resolved_at is not null
            then date_diff('second', created_at, resolved_at)
    end as resolution_seconds
from {{ source('agentic_commerce', 'intent_event') }}
