-- Vault-style link between Person and Visit Occurrence.
{{ config(materialized='ephemeral') }}

with src as (
    select visit_occurrence_id, person_id
    from {{ ref('stg_real_world_evidence__visit_occurrence') }}
    where visit_occurrence_id is not null and person_id is not null
)

select
    md5(cast(person_id as varchar) || '|' || cast(visit_occurrence_id as varchar)) as l_person_visit_hk,
    md5(cast(person_id as varchar))                  as h_person_hk,
    md5(cast(visit_occurrence_id as varchar))        as h_visit_hk,
    current_date                                     as load_date,
    'real_world_evidence.visit_occurrence'           as record_source
from src
group by person_id, visit_occurrence_id
