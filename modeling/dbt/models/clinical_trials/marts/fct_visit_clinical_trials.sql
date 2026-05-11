-- Grain: one row per subject-visit instance from SDTM SV.
{{ config(materialized='table') }}

with v as (select * from {{ ref('stg_clinical_trials__visit') }}),
     hub_s as (select * from {{ ref('int_clinical_trials__hub_subject') }}),
     lnk as (select * from {{ ref('int_clinical_trials__link_subject_site') }})

select
    v.visit_bk                                          as visit_key,
    hub_s.h_subject_hk                                  as subject_key,
    lnk.h_study_hk                                      as study_key,
    lnk.h_site_hk                                       as site_key,
    cast({{ format_date('v.svstdtc', '%Y%m%d') }} as integer)      as visit_date_key,
    v.visit                                             as visit_label,
    v.visitnum                                          as visit_num,
    v.svstdtc                                           as visit_start_dt,
    v.svendtc                                           as visit_end_dt,
    v.svstatus                                          as visit_status,
    case when v.svstatus = 'completed' then true else false end as completed
from v
left join hub_s on hub_s.subject_bk    = v.usubjid
left join lnk   on lnk.h_subject_hk    = hub_s.h_subject_hk
