-- Staging: OMOP Condition Occurrence.
{{ config(materialized='view') }}

select
    cast(condition_occurrence_id     as bigint)    as condition_occurrence_id,
    cast(person_id                   as bigint)    as person_id,
    cast(condition_concept_id        as bigint)    as condition_concept_id,
    cast(condition_start_date        as date)      as condition_start_date,
    cast(condition_start_datetime    as timestamp) as condition_start_datetime,
    cast(condition_end_date          as date)      as condition_end_date,
    cast(condition_type_concept_id   as bigint)    as condition_type_concept_id,
    cast(stop_reason                 as varchar)   as stop_reason,
    cast(provider_id                 as bigint)    as provider_id,
    cast(visit_occurrence_id         as bigint)    as visit_occurrence_id,
    cast(condition_source_value      as varchar)   as condition_source_value,
    cast(condition_status_concept_id as bigint)    as condition_status_concept_id
from {{ source('real_world_evidence', 'condition_occurrence') }}
