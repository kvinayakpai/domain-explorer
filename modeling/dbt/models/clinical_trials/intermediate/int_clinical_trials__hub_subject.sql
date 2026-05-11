-- Vault-style hub for the Subject business key (USUBJID).
{{ config(materialized='ephemeral') }}

with src as (
    select usubjid, rficdtc
    from {{ ref('stg_clinical_trials__subject') }}
    where usubjid is not null
)

select
    md5(usubjid)                          as h_subject_hk,
    usubjid                               as subject_bk,
    coalesce(min(rficdtc), current_date)  as load_date,
    'clinical_trials.subject'             as record_source
from src
group by usubjid
