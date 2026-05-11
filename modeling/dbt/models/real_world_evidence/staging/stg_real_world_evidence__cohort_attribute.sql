-- Staging: OMOP Cohort Attribute.
{{ config(materialized='view') }}

select
    cast(cohort_definition_id    as bigint)  as cohort_definition_id,
    cast(subject_id              as bigint)  as subject_id,
    cast(cohort_start_date       as date)    as cohort_start_date,
    cast(attribute_definition_id as bigint)  as attribute_definition_id,
    cast(value_as_number         as double)  as value_as_number,
    cast(value_as_concept_id     as bigint)  as value_as_concept_id
from {{ source('real_world_evidence', 'cohort_attribute') }}
