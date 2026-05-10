{{ config(materialized='view') }}

select
    cast(dispute_id              as varchar)    as dispute_id,
    cast(agent_txn_id            as varchar)    as agent_txn_id,
    cast(reason_code             as varchar)    as reason_code,
    cast(opened_at               as timestamp)  as opened_at,
    cast(resolved_at             as timestamp)  as resolved_at,
    cast(amount_minor            as bigint)     as amount_minor,
    upper(currency)                              as currency,
    cast(outcome                 as varchar)    as outcome,
    cast(carryback_to_operator   as boolean)    as carryback_to_operator
from {{ source('agentic_commerce', 'dispute') }}
