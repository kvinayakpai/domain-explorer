-- Staging: OMOP concept reference.
{{ config(materialized='view') }}

select
    cast(concept_id        as bigint)  as concept_id,
    cast(concept_name      as varchar) as concept_name,
    cast(domain_id         as varchar) as domain_id,
    cast(vocabulary_id     as varchar) as vocabulary_id,
    cast(concept_class_id  as varchar) as concept_class_id,
    cast(standard_concept  as varchar) as standard_concept
from {{ source('real_world_evidence', 'concept') }}
