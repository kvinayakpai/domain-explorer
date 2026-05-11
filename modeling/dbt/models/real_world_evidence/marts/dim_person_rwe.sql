-- Person dimension for real_world_evidence (OMOP).
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_real_world_evidence__hub_person') }}),
     sat as (select * from {{ ref('int_real_world_evidence__sat_person') }}),
     stg as (select * from {{ ref('stg_real_world_evidence__person') }})

select
    h.h_person_hk         as person_key,
    h.person_bk           as person_id,
    s.gender_concept_id,
    s.year_of_birth,
    s.month_of_birth,
    s.day_of_birth,
    s.race_concept_id,
    s.ethnicity_concept_id,
    s.location_id,
    s.provider_id,
    s.care_site_id,
    s.age_group,
    stg.person_source_value,
    h.load_date           as dim_loaded_at
from hub h
left join sat s   on s.h_person_hk = h.h_person_hk
left join stg     on stg.person_id = h.person_bk
