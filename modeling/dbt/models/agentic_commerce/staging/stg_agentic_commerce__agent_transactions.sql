{{ config(materialized='view') }}

select
    cast(agent_txn_id      as varchar)    as agent_txn_id,
    cast(cart_id           as varchar)    as cart_id,
    cast(grant_id          as varchar)    as grant_id,
    cast(agent_id          as varchar)    as agent_id,
    cast(principal_id      as varchar)    as principal_id,
    cast(merchant_id       as varchar)    as merchant_id,
    cast(psp               as varchar)    as psp,
    cast(rail              as varchar)    as rail,
    cast(scheme            as varchar)    as scheme,
    cast(agent_indicator   as varchar)    as agent_indicator,
    cast(amount_minor      as bigint)     as amount_minor,
    upper(currency)                        as currency,
    cast(stepup_method     as varchar)    as stepup_method,
    cast(status            as varchar)    as status,
    cast(authorized_at     as timestamp)  as authorized_at,
    cast(captured_at       as timestamp)  as captured_at,
    cast(decline_reason    as varchar)    as decline_reason,
    cast(latency_ms        as integer)    as latency_ms,
    case when status in ('captured','refunded','disputed') then true else false end as is_captured,
    case when status = 'declined'  then true else false end as is_declined,
    case when status = 'refunded'  then true else false end as is_refunded,
    case when status = 'disputed'  then true else false end as is_disputed,
    case when stepup_method <> 'none' then true else false end as is_stepup
from {{ source('agentic_commerce', 'agent_transaction') }}
