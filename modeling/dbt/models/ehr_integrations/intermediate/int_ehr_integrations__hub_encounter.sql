-- Vault-style hub for the FHIR Encounter business key.
{{ config(materialized='ephemeral') }}

with src as (
    select encounter_id, period_start
    from {{ ref('stg_ehr_integrations__encounter') }}
    where encounter_id is not null
)

select
    md5(encounter_id)                                          as h_encounter_hk,
    encounter_id                                               as encounter_bk,
    coalesce(min(cast(period_start as date)), current_date)    as load_date,
    'ehr_integrations.encounter'                               as record_source
from src
group by encounter_id
