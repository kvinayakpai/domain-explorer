-- Vault-style hub for the FHIR Patient business key.
{{ config(materialized='ephemeral') }}

with src as (
    select patient_id, birth_date
    from {{ ref('stg_ehr_integrations__patient') }}
    where patient_id is not null
)

select
    md5(patient_id)                    as h_patient_hk,
    patient_id                         as patient_bk,
    coalesce(min(birth_date), current_date) as load_date,
    'ehr_integrations.patient'         as record_source
from src
group by patient_id
