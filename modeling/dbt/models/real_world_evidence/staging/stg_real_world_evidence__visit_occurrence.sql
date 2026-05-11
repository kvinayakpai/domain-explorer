-- Staging: OMOP Visit Occurrence.
{{ config(materialized='view') }}

select
    cast(visit_occurrence_id          as bigint)    as visit_occurrence_id,
    cast(person_id                    as bigint)    as person_id,
    cast(visit_concept_id             as bigint)    as visit_concept_id,
    cast(visit_start_date             as date)      as visit_start_date,
    cast(visit_start_datetime         as timestamp) as visit_start_datetime,
    cast(visit_end_date               as date)      as visit_end_date,
    cast(visit_end_datetime           as timestamp) as visit_end_datetime,
    cast(visit_type_concept_id        as bigint)    as visit_type_concept_id,
    cast(provider_id                  as bigint)    as provider_id,
    cast(care_site_id                 as bigint)    as care_site_id,
    cast(visit_source_value           as varchar)   as visit_source_value,
    cast(admitting_source_concept_id  as bigint)    as admitting_source_concept_id,
    cast(discharge_to_concept_id      as bigint)    as discharge_to_concept_id
from {{ source('real_world_evidence', 'visit_occurrence') }}
