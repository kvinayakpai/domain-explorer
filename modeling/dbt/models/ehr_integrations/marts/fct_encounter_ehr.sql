-- Grain: one row per FHIR Encounter.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_ehr_integrations__hub_encounter') }}),
     sat as (select * from {{ ref('int_ehr_integrations__sat_encounter') }}),
     lnk as (select * from {{ ref('int_ehr_integrations__link_patient_encounter') }}),
     conds as (
        select encounter_id, count(*) as condition_count
        from {{ ref('stg_ehr_integrations__condition') }}
        group by encounter_id
     ),
     procs as (
        select encounter_id, count(*) as procedure_count
        from {{ ref('stg_ehr_integrations__procedure') }}
        group by encounter_id
     ),
     mreqs as (
        select encounter_id, count(*) as medication_request_count
        from {{ ref('stg_ehr_integrations__medication_request') }}
        group by encounter_id
     )

select
    h.h_encounter_hk                                       as encounter_key,
    h.encounter_bk                                         as encounter_id,
    cast({{ format_date('s.period_start', '%Y%m%d') }} as integer)    as start_date_key,
    s.period_start                                         as period_start,
    s.period_end                                           as period_end,
    s.length_minutes,
    s.status,
    s.class_code,
    s.type_code,
    lnk.h_patient_hk                                       as patient_key,
    lnk.h_practitioner_hk                                  as primary_practitioner_key,
    coalesce(conds.condition_count, 0)                     as condition_count,
    coalesce(procs.procedure_count, 0)                     as procedure_count,
    coalesce(mreqs.medication_request_count, 0)            as medication_request_count
from hub h
join sat s on s.h_encounter_hk = h.h_encounter_hk
left join lnk on lnk.h_encounter_hk = h.h_encounter_hk
left join conds on conds.encounter_id = h.encounter_bk
left join procs on procs.encounter_id = h.encounter_bk
left join mreqs on mreqs.encounter_id = h.encounter_bk
