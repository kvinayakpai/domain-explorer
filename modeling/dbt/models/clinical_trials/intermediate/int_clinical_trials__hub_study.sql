-- Vault-style hub for the Study business key.
{{ config(materialized='ephemeral') }}

with src as (
    select studyid, started_at
    from {{ ref('stg_clinical_trials__study') }}
    where studyid is not null
)

select
    md5(studyid)                            as h_study_hk,
    studyid                                 as study_bk,
    coalesce(min(started_at), current_date) as load_date,
    'clinical_trials.study'                 as record_source
from src
group by studyid
