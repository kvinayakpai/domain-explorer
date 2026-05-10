{{ config(materialized='view') }}

select
    cast(agent_id        as varchar)    as agent_id,
    cast(aaid            as varchar)    as aaid,
    cast(operator_org    as varchar)    as operator_org,
    cast(agent_kind      as varchar)    as agent_kind,
    cast(model_family    as varchar)    as model_family,
    cast(kya_status      as varchar)    as kya_status,
    cast(kya_trust_score as double)     as kya_trust_score,
    cast(created_at      as timestamp)  as created_at,
    cast(status          as varchar)    as status
from {{ source('agentic_commerce', 'agent') }}
