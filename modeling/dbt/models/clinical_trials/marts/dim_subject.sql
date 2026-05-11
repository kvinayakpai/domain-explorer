-- Subject dimension fed from the Vault hub/sat + link to study/site.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_clinical_trials__hub_subject') }}),
     sat as (select * from {{ ref('int_clinical_trials__sat_subject') }}),
     lnk as (select * from {{ ref('int_clinical_trials__link_subject_site') }})

select
    h.h_subject_hk         as subject_key,
    h.subject_bk           as usubjid,
    s.armcd,
    s.actarmcd,
    s.sex,
    s.race,
    s.ethnic,
    s.country,
    s.age,
    s.age_band,
    s.rfstdtc,
    s.rfendtc,
    s.dthfl,
    l.h_study_hk           as study_key,
    l.h_site_hk            as site_key,
    h.load_date            as dim_loaded_at
from hub h
left join sat s on s.h_subject_hk = h.h_subject_hk
left join lnk l on l.h_subject_hk = h.h_subject_hk
