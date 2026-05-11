-- Staging: FHIR Encounter.
{{ config(materialized='view') }}

select
    cast(encounter_id              as varchar)   as encounter_id,
    cast(patient_id                as varchar)   as patient_id,
    cast(status                    as varchar)   as status,
    cast(class_code                as varchar)   as class_code,
    cast(type_code                 as varchar)   as type_code,
    cast(primary_practitioner_id   as varchar)   as primary_practitioner_id,
    cast(service_provider_org_id   as varchar)   as service_provider_org_id,
    cast(period_start              as timestamp) as period_start,
    cast(period_end                as timestamp) as period_end,
    cast(length_minutes            as integer)   as length_minutes
from {{ source('ehr_integrations', 'encounter') }}
