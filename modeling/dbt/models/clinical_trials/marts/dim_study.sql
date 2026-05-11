-- Study dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_clinical_trials__hub_study') }}),
     stg as (select * from {{ ref('stg_clinical_trials__study') }})

select
    h.h_study_hk            as study_key,
    h.study_bk              as studyid,
    s.study_title,
    s.therapeutic_area,
    s.phase,
    s.indication,
    s.blinding,
    s.status,
    s.started_at,
    s.primary_completion_date,
    h.load_date             as dim_loaded_at
from hub h
left join stg s on s.studyid = h.study_bk
