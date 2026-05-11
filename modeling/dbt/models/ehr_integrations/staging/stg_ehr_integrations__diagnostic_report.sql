-- Staging: FHIR DiagnosticReport.
{{ config(materialized='view') }}

select
    cast(diagnostic_report_id  as varchar)   as diagnostic_report_id,
    cast(patient_id            as varchar)   as patient_id,
    cast(encounter_id          as varchar)   as encounter_id,
    cast(status                as varchar)   as status,
    cast(category_code         as varchar)   as category_code,
    cast(code_system           as varchar)   as code_system,
    cast(code_value            as varchar)   as code_value,
    cast(effective_date_time   as timestamp) as effective_ts,
    cast(performer_org_id      as varchar)   as performer_org_id,
    cast(results_interpreter_id as varchar)  as results_interpreter_id
from {{ source('ehr_integrations', 'diagnostic_report') }}
