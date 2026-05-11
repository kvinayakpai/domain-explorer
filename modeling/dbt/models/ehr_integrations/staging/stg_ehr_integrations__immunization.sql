-- Staging: FHIR Immunization (CVX-coded).
{{ config(materialized='view') }}

select
    cast(immunization_id        as varchar)   as immunization_id,
    cast(patient_id             as varchar)   as patient_id,
    cast(encounter_id           as varchar)   as encounter_id,
    cast(status                 as varchar)   as status,
    cast(vaccine_code_system    as varchar)   as vaccine_code_system,
    cast(vaccine_code_value     as varchar)   as cvx_code,
    cast(occurrence_date_time   as timestamp) as occurrence_ts,
    cast(lot_number             as varchar)   as lot_number,
    cast(site_code              as varchar)   as site_code,
    cast(route_code             as varchar)   as route_code,
    cast(dose_quantity          as double)    as dose_quantity,
    cast(dose_quantity_unit     as varchar)   as dose_quantity_unit,
    cast(performer_id           as varchar)   as performer_id
from {{ source('ehr_integrations', 'immunization') }}
