-- Patient dimension for ehr_integrations.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_ehr_integrations__hub_patient') }}),
     stg as (select * from {{ ref('stg_ehr_integrations__patient') }})

select
    h.h_patient_hk             as patient_key,
    h.patient_bk               as patient_id,
    s.identifier_mrn,
    s.family_name,
    s.given_names,
    s.gender,
    s.birth_date,
    s.age_years,
    s.marital_status_code,
    s.race_code,
    s.ethnicity_code,
    s.address_state,
    s.address_country,
    s.language_code,
    s.managing_organization_id,
    h.load_date                as dim_loaded_at
from hub h
left join stg s on s.patient_id = h.patient_bk
