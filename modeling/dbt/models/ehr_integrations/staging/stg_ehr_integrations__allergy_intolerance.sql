-- Staging: FHIR AllergyIntolerance.
{{ config(materialized='view') }}

select
    cast(allergy_id                as varchar)   as allergy_id,
    cast(patient_id                as varchar)   as patient_id,
    cast(clinical_status_code      as varchar)   as clinical_status_code,
    cast(verification_status_code  as varchar)   as verification_status_code,
    cast(type                      as varchar)   as type,
    cast(category                  as varchar)   as category,
    cast(criticality               as varchar)   as criticality,
    cast(substance_code_value      as varchar)   as substance_code_value,
    cast(substance_display         as varchar)   as substance_display,
    cast(reaction_severity         as varchar)   as reaction_severity,
    cast(onset_date_time           as timestamp) as onset_ts
from {{ source('ehr_integrations', 'allergy_intolerance') }}
