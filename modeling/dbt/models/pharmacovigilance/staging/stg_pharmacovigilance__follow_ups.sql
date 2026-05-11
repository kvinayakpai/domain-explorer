-- Staging: PV case follow-ups.
{{ config(materialized='view') }}

select
    cast(followup_id         as varchar)   as followup_id,
    cast(case_id             as varchar)   as case_id,
    cast(received_at         as timestamp) as received_at,
    cast(type                as varchar)   as type,
    cast(completeness_score  as double)    as completeness_score
from {{ source('pharmacovigilance', 'follow_ups') }}
