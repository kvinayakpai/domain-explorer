{{ config(materialized='view') }}

select
    cast(grant_id                       as varchar)    as grant_id,
    cast(principal_id                   as varchar)    as principal_id,
    cast(agent_id                       as varchar)    as agent_id,
    cast(rar_type                       as varchar)    as rar_type,
    cast(max_amount_minor               as bigint)     as max_amount_minor,
    upper(max_amount_currency)                          as max_amount_currency,
    cast(merchant_scope                 as varchar)    as merchant_scope,
    cast(category_scope                 as varchar)    as category_scope,
    cast(per_txn_cap_minor              as bigint)     as per_txn_cap_minor,
    cast(scope_expires_at               as timestamp)  as scope_expires_at,
    cast(stepup_required_above_minor    as bigint)     as stepup_required_above_minor,
    cast(issued_at                      as timestamp)  as issued_at,
    cast(revoked_at                     as timestamp)  as revoked_at,
    cast(status                         as varchar)    as status
from {{ source('agentic_commerce', 'authorization_grant') }}
