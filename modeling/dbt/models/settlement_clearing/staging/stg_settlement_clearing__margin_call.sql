-- Staging: margin call.
{{ config(materialized='view') }}

select
    cast(margin_call_id   as varchar)   as margin_call_id,
    cast(calling_party_id as varchar)   as calling_party_id,
    cast(called_party_id  as varchar)   as called_party_id,
    cast(call_type        as varchar)   as call_type,
    cast(call_amount      as double)    as call_amount,
    upper(call_currency)                as call_currency,
    cast(issued_at        as timestamp) as issued_at,
    cast(due_at           as timestamp) as due_at,
    cast(status           as varchar)   as status
from {{ source('settlement_clearing', 'margin_call') }}
