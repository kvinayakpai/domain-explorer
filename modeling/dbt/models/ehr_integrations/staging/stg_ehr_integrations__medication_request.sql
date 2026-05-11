-- Staging: FHIR MedicationRequest (RxNorm).
{{ config(materialized='view') }}

select
    cast(medication_request_id   as varchar)   as medication_request_id,
    cast(patient_id              as varchar)   as patient_id,
    cast(encounter_id            as varchar)   as encounter_id,
    cast(requester_id            as varchar)   as requester_id,
    cast(status                  as varchar)   as status,
    cast(intent                  as varchar)   as intent,
    cast(priority                as varchar)   as priority,
    cast(medication_code_system  as varchar)   as medication_code_system,
    cast(medication_code_value   as varchar)   as rxnorm_code,
    cast(medication_display      as varchar)   as medication_display,
    cast(dose_quantity_value     as double)    as dose_quantity_value,
    cast(dose_quantity_unit      as varchar)   as dose_quantity_unit,
    cast(route_code              as varchar)   as route_code,
    cast(frequency_text          as varchar)   as frequency_text,
    cast(authored_on             as timestamp) as authored_on,
    cast(dispense_quantity       as double)    as dispense_quantity,
    cast(dispense_refills_allowed as integer)  as dispense_refills_allowed,
    cast(substitution_allowed    as boolean)   as substitution_allowed
from {{ source('ehr_integrations', 'medication_request') }}
