-- Staging: FHIR Condition (ICD-10-CM coded).
{{ config(materialized='view') }}

select
    cast(condition_id              as varchar)   as condition_id,
    cast(patient_id                as varchar)   as patient_id,
    cast(encounter_id              as varchar)   as encounter_id,
    cast(clinical_status_code      as varchar)   as clinical_status_code,
    cast(verification_status_code  as varchar)   as verification_status_code,
    cast(category_code             as varchar)   as category_code,
    cast(severity_code             as varchar)   as severity_code,
    cast(code_system               as varchar)   as code_system,
    cast(code_value                as varchar)   as icd10_code,
    cast(code_display              as varchar)   as code_display,
    cast(onset_date_time           as timestamp) as onset_ts,
    cast(recorded_date             as date)      as recorded_date
from {{ source('ehr_integrations', 'condition') }}
