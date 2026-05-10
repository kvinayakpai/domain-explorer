{{ config(materialized='table') }}

select
    row_number() over (order by agent_id)        as agent_sk,
    agent_id,
    aaid,
    operator_org,
    agent_kind,
    model_family,
    kya_status,
    kya_trust_score,
    status,
    created_at                                   as valid_from,
    cast(null as timestamp)                      as valid_to,
    true                                         as is_current
from {{ ref('stg_agentic_commerce__agents') }}
