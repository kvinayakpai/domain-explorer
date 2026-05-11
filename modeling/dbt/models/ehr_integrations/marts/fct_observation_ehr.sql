-- Grain: one row per FHIR Observation result (LOINC labs/vitals).
{{ config(materialized='table') }}

with obs as (select * from {{ ref('stg_ehr_integrations__observation') }})

select
    obs.observation_id                                  as observation_id,
    md5(obs.observation_id)                             as observation_key,
    md5(obs.patient_id)                                 as patient_key,
    case when obs.encounter_id is not null
         then md5(obs.encounter_id) end                 as encounter_key,
    case when obs.performer_id is not null
         then md5(obs.performer_id) end                 as performer_key,
    cast({{ format_date('obs.effective_ts', '%Y%m%d') }} as integer) as effective_date_key,
    obs.effective_ts                                    as effective_ts,
    obs.issued_ts,
    obs.status,
    obs.category_code,
    obs.loinc_code,
    obs.code_display,
    obs.value_quantity,
    obs.value_unit,
    obs.interpretation_code,
    obs.reference_range_low,
    obs.reference_range_high,
    obs.is_abnormal
from obs
