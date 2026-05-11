-- Patient dimension for pharmacovigilance.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_pharmacovigilance__hub_patient') }}),
     stg as (select * from {{ ref('stg_pharmacovigilance__patients') }})

select
    h.h_patient_hk    as patient_key,
    h.patient_bk      as patient_id,
    s.age,
    s.age_group,
    s.sex,
    s.weight_kg,
    s.country,
    s.pregnancy_status,
    h.load_date       as dim_loaded_at
from hub h
left join stg s on s.patient_id = h.patient_bk
