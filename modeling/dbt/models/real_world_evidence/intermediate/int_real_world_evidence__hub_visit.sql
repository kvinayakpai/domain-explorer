-- Vault-style hub for the OMOP Visit Occurrence business key.
{{ config(materialized='ephemeral') }}

with src as (
    select visit_occurrence_id, visit_start_date
    from {{ ref('stg_real_world_evidence__visit_occurrence') }}
    where visit_occurrence_id is not null
)

select
    md5(cast(visit_occurrence_id as varchar)) as h_visit_hk,
    visit_occurrence_id                       as visit_bk,
    coalesce(min(visit_start_date), current_date) as load_date,
    'real_world_evidence.visit_occurrence'    as record_source
from src
group by visit_occurrence_id
