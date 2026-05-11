-- Vault-style hub for the Patient business key.
{{ config(materialized='ephemeral') }}

with src as (
    select patient_id
    from {{ ref('stg_pharmacovigilance__patients') }}
    where patient_id is not null
)

select
    md5(patient_id)                 as h_patient_hk,
    patient_id                      as patient_bk,
    current_date                    as load_date,
    'pharmacovigilance.patients'    as record_source
from src
group by patient_id
