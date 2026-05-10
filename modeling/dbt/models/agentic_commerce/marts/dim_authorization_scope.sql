{{ config(materialized='table') }}

select
    row_number() over (order by grant_id) as scope_sk,
    grant_id,
    rar_type,
    max_amount_minor,
    max_amount_currency,
    per_txn_cap_minor,
    stepup_required_above_minor,
    scope_expires_at,
    status
from {{ ref('stg_agentic_commerce__authorization_grants') }}
