-- Staging: OMOP Procedure Occurrence.
{{ config(materialized='view') }}

select
    cast(procedure_occurrence_id     as bigint)    as procedure_occurrence_id,
    cast(person_id                   as bigint)    as person_id,
    cast(procedure_concept_id        as bigint)    as procedure_concept_id,
    cast(procedure_date              as date)      as procedure_date,
    cast(procedure_datetime          as timestamp) as procedure_datetime,
    cast(procedure_type_concept_id   as bigint)    as procedure_type_concept_id,
    cast(modifier_concept_id         as bigint)    as modifier_concept_id,
    cast(quantity                    as integer)   as quantity,
    cast(provider_id                 as bigint)    as provider_id,
    cast(visit_occurrence_id         as bigint)    as visit_occurrence_id,
    cast(procedure_source_value      as varchar)   as procedure_source_value
from {{ source('real_world_evidence', 'procedure_occurrence') }}
