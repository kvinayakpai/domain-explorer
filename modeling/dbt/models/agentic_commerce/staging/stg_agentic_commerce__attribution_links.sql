{{ config(materialized='view') }}

select
    cast(attribution_id    as varchar)    as attribution_id,
    cast(intent_id         as varchar)    as intent_id,
    cast(agent_txn_id      as varchar)    as agent_txn_id,
    cast(model             as varchar)    as model,
    cast(weight            as double)     as weight,
    cast(lookback_seconds  as integer)    as lookback_seconds,
    cast(created_at        as timestamp)  as created_at
from {{ source('agentic_commerce', 'attribution_link') }}
