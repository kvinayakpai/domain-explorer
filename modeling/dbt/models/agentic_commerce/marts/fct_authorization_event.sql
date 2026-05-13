{{ config(materialized='table') }}

with g as (select * from {{ ref('stg_agentic_commerce__authorization_grants') }}),
     a as (select * from {{ ref('dim_agent') }}),
     p as (select * from {{ ref('dim_principal') }}),
     s as (select * from {{ ref('dim_authorization_scope') }})

-- Issued event
select
    g.grant_id || '-issued' as grant_event_id,
    g.grant_id,
    cast({{ format_date('g.issued_at', '%Y%m%d') }} as integer) as date_key,
    a.agent_sk,
    p.principal_sk,
    s.scope_sk,
    'issued' as event_type,
    g.max_amount_minor as delta_amount_minor,
    g.issued_at as occurred_at
from g
left join a on a.agent_id     = g.agent_id
left join p on p.principal_id = g.principal_id
left join s on s.grant_id     = g.grant_id

union all

-- Revoked event (where applicable)
select
    g.grant_id || '-revoked' as grant_event_id,
    g.grant_id,
    cast({{ format_date('g.revoked_at', '%Y%m%d') }} as integer) as date_key,
    a.agent_sk,
    p.principal_sk,
    s.scope_sk,
    'revoked' as event_type,
    cast(0 as bigint) as delta_amount_minor,
    g.revoked_at as occurred_at
from g
left join a on a.agent_id     = g.agent_id
left join p on p.principal_id = g.principal_id
left join s on s.grant_id     = g.grant_id
where g.revoked_at is not null
