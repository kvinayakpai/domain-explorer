-- Staging: regulatory submissions tied to a case.
{{ config(materialized='view') }}

select
    cast(submission_id as varchar)   as submission_id,
    cast(case_id       as varchar)   as case_id,
    cast(agency        as varchar)   as agency,
    cast(format        as varchar)   as format,
    cast(submitted_at  as timestamp) as submitted_at,
    cast(ack_status    as varchar)   as ack_status
from {{ source('pharmacovigilance', 'regulatory_submissions') }}
