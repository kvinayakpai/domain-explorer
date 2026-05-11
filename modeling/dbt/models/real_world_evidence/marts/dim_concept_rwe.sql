-- Concept dimension for real_world_evidence (OMOP vocabulary subset).
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_real_world_evidence__concept') }})

select
    md5(cast(concept_id as varchar)) as concept_key,
    concept_id,
    concept_name,
    domain_id,
    vocabulary_id,
    concept_class_id,
    standard_concept,
    current_date                     as dim_loaded_at
from stg
