-- Staging: FHIR Observation (LOINC labs + vitals).
{{ config(materialized='view') }}

select
    cast(observation_id        as varchar)   as observation_id,
    cast(patient_id            as varchar)   as patient_id,
    cast(encounter_id          as varchar)   as encounter_id,
    cast(status                as varchar)   as status,
    cast(category_code         as varchar)   as category_code,
    cast(code_system           as varchar)   as code_system,
    cast(code_value            as varchar)   as loinc_code,
    cast(code_display          as varchar)   as code_display,
    cast(effective_date_time   as timestamp) as effective_ts,
    cast(issued                as timestamp) as issued_ts,
    cast(value_quantity_value  as double)    as value_quantity,
    cast(value_quantity_unit   as varchar)   as value_unit,
    cast(interpretation_code   as varchar)   as interpretation_code,
    cast(reference_range_low   as double)    as reference_range_low,
    cast(reference_range_high  as double)    as reference_range_high,
    cast(performer_id          as varchar)   as performer_id,
    case when cast(interpretation_code as varchar) in ('H','L') then true else false end as is_abnormal
from {{ source('ehr_integrations', 'observation') }}
