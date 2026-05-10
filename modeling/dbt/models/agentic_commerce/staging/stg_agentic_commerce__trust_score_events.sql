{{ config(materialized='view') }}

select
    cast(trust_event_id  as varchar)    as trust_event_id,
    cast(agent_id        as varchar)    as agent_id,
    cast(source          as varchar)    as source,
    cast(score           as double)     as score,
    cast(signal_summary  as varchar)    as signal_summary,
    cast(observed_at     as timestamp)  as observed_at
from {{ source('agentic_commerce', 'trust_score_event') }}
