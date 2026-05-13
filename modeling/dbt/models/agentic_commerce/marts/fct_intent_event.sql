{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_agentic_commerce__intent_events') }}),
     a as (select * from {{ ref('dim_agent') }}),
     p as (select * from {{ ref('dim_principal') }})

select
    i.intent_id,
    cast({{ format_date('i.created_at', '%Y%m%d') }} as integer) as date_key,
    a.agent_sk,
    p.principal_sk,
    i.session_id,
    i.state,
    i.category_hint,
    i.budget_min_minor,
    i.budget_max_minor,
    i.budget_currency,
    i.deadline_ts,
    case when i.state = 'fulfilled' then true else false end as fulfilled,
    case when i.state = 'abandoned' then true else false end as abandoned,
    i.resolution_seconds as intent_to_purchase_seconds,
    i.created_at,
    i.resolved_at
from i
left join a on a.agent_id     = i.agent_id
left join p on p.principal_id = i.principal_id
