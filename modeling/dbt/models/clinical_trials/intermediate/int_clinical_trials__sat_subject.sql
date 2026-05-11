-- Vault-style satellite carrying descriptive Subject attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_clinical_trials__subject') }}
)

select
    md5(usubjid)                                  as h_subject_hk,
    coalesce(rficdtc, current_date)               as load_date,
    md5(coalesce(armcd,'') || '|' || coalesce(actarmcd,'')
        || '|' || coalesce(sex,'') || '|' || coalesce(race,'')
        || '|' || coalesce(country,''))           as hashdiff,
    armcd,
    actarmcd,
    sex,
    race,
    ethnic,
    country,
    age,
    age_band,
    rfstdtc,
    rfendtc,
    rficdtc,
    dthfl,
    'clinical_trials.subject'                     as record_source
from src
