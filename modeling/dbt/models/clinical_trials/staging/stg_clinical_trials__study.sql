-- Staging: study (protocol) master.
{{ config(materialized='view') }}

select
    cast(studyid                  as varchar) as studyid,
    cast(study_title              as varchar) as study_title,
    cast(therapeutic_area         as varchar) as therapeutic_area,
    cast(phase                    as varchar) as phase,
    cast(indication               as varchar) as indication,
    cast(blinding                 as varchar) as blinding,
    cast(started_at               as date)    as started_at,
    cast(primary_completion_date  as date)    as primary_completion_date,
    cast(status                   as varchar) as status
from {{ source('clinical_trials', 'study') }}
