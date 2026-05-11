-- Practitioner dimension for ehr_integrations.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_ehr_integrations__hub_practitioner') }}),
     stg as (select * from {{ ref('stg_ehr_integrations__practitioner') }})

select
    h.h_practitioner_hk        as practitioner_key,
    h.practitioner_bk          as practitioner_id,
    s.npi,
    s.family_name,
    s.given_names,
    s.gender,
    s.qualification_code,
    s.qualification_issuer_org_id,
    s.active,
    h.load_date                as dim_loaded_at
from hub h
left join stg s on s.practitioner_id = h.practitioner_bk
