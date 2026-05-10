{{ config(materialized='view') }}

select
    cast(tool_call_id       as varchar)    as tool_call_id,
    cast(session_id         as varchar)    as session_id,
    cast(intent_id          as varchar)    as intent_id,
    cast(server_name        as varchar)    as server_name,
    cast(tool_name          as varchar)    as tool_name,
    cast(started_at         as timestamp)  as started_at,
    cast(latency_ms         as integer)    as latency_ms,
    cast(cost_usd           as double)     as cost_usd,
    cast(status             as varchar)    as status,
    cast(input_size_bytes   as integer)    as input_size_bytes,
    cast(output_size_bytes  as integer)    as output_size_bytes,
    case when status = 'error' then true else false end as is_error,
    case when status = 'timeout' then true else false end as is_timeout,
    case when status = 'denied' then true else false end as is_denied
from {{ source('agentic_commerce', 'tool_call') }}
