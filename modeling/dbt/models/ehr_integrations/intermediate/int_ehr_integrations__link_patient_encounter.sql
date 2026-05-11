-- Vault-style link from Encounter to Patient and primary Practitioner.
{{ config(materialized='ephemeral') }}

with src as (
    select encounter_id, patient_id, primary_practitioner_id
    from {{ ref('stg_ehr_integrations__encounter') }}
    where encounter_id is not null and patient_id is not null
)

select
    md5(encounter_id || '|' || patient_id)  as l_patient_encounter_hk,
    md5(encounter_id)                        as h_encounter_hk,
    md5(patient_id)                          as h_patient_hk,
    case when primary_practitioner_id is not null
         then md5(primary_practitioner_id) end as h_practitioner_hk,
    current_date                             as load_date,
    'ehr_integrations.encounter'             as record_source
from src
group by encounter_id, patient_id, primary_practitioner_id
