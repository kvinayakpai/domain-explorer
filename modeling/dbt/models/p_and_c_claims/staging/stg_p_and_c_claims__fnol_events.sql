-- Staging: first-notice-of-loss intake events.
{{ config(materialized='view') }}

select
    cast(fnol_event_id    as varchar)   as fnol_event_id,
    cast(claim_id         as varchar)   as claim_id,
    cast(channel          as varchar)   as channel,
    cast(duration_minutes as double)    as duration_minutes,
    cast(language         as varchar)   as language_code,
    cast(received_at      as timestamp) as received_at
from {{ source('p_and_c_claims', 'fnol_events') }}
