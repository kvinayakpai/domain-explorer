-- Vault-style satellite carrying descriptive Encounter attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_ehr_integrations__encounter') }}
)

select
    md5(encounter_id)                                         as h_encounter_hk,
    period_start                                              as load_ts,
    md5(coalesce(status,'') || '|' || coalesce(class_code,'')
        || '|' || coalesce(type_code,'') || '|' || cast(length_minutes as varchar))
                                                              as hashdiff,
    status,
    class_code,
    type_code,
    period_start,
    period_end,
    length_minutes,
    'ehr_integrations.encounter'                              as record_source
from src
