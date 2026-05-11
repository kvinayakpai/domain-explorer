-- Staging: FHIR Procedure (CPT-coded).
{{ config(materialized='view') }}

select
    cast(procedure_id          as varchar)   as procedure_id,
    cast(patient_id            as varchar)   as patient_id,
    cast(encounter_id          as varchar)   as encounter_id,
    cast(status                as varchar)   as status,
    cast(code_system           as varchar)   as code_system,
    cast(code_value            as varchar)   as cpt_code,
    cast(code_display          as varchar)   as code_display,
    cast(performed_period_start as timestamp) as period_start,
    cast(performed_period_end   as timestamp) as period_end,
    cast(performer_id          as varchar)   as performer_id,
    cast(outcome_code          as varchar)   as outcome_code
from {{ source('ehr_integrations', 'procedure') }}
