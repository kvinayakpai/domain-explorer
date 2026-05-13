{{ config(materialized='view') }}

select
    cast(session_id        as varchar)    as session_id,
    cast(agent_id          as varchar)    as agent_id,
    cast(principal_id      as varchar)    as principal_id,
    cast(grant_id          as varchar)    as grant_id,
    cast(started_at        as timestamp)  as started_at,
    cast(ended_at          as timestamp)  as ended_at,
    cast(client_signature  as varchar)    as client_signature,
    cast(principal_present as boolean)    as principal_present,
    case
        when ended_at is not null
            then {{ dbt_utils.datediff('started_at', 'ended_at', 'second') }}
    end as duration_seconds
from {{ source('agentic_commerce', 'agent_session') }}
