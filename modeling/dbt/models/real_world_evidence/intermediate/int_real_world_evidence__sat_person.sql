-- Vault-style satellite carrying descriptive Person attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_real_world_evidence__person') }}
)

select
    md5(cast(person_id as varchar))                       as h_person_hk,
    current_date                                          as load_date,
    md5(cast(gender_concept_id as varchar)
        || '|' || cast(year_of_birth as varchar)
        || '|' || cast(race_concept_id as varchar)
        || '|' || cast(ethnicity_concept_id as varchar))  as hashdiff,
    gender_concept_id,
    year_of_birth,
    month_of_birth,
    day_of_birth,
    race_concept_id,
    ethnicity_concept_id,
    location_id,
    provider_id,
    care_site_id,
    age_group,
    'real_world_evidence.person'                          as record_source
from src
