-- Staging: OMOP Cohort.
{{ config(materialized='view') }}

select
    cast(cohort_definition_id  as bigint) as cohort_definition_id,
    cast(subject_id            as bigint) as subject_id,
    cast(cohort_start_date     as date)   as cohort_start_date,
    cast(cohort_end_date       as date)   as cohort_end_date
from {{ source('real_world_evidence', 'cohort') }}
