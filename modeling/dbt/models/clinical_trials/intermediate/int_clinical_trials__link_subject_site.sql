-- Vault-style link between Subject, Site, and Study.
{{ config(materialized='ephemeral') }}

with src as (
    select usubjid, siteid, studyid
    from {{ ref('stg_clinical_trials__subject') }}
    where usubjid is not null and siteid is not null and studyid is not null
)

select
    md5(usubjid || '|' || siteid || '|' || studyid) as l_subject_site_hk,
    md5(usubjid)  as h_subject_hk,
    md5(siteid)   as h_site_hk,
    md5(studyid)  as h_study_hk,
    current_date  as load_date,
    'clinical_trials.subject' as record_source
from src
group by usubjid, siteid, studyid
