-- Vault-style hub for the FHIR Practitioner business key.
{{ config(materialized='ephemeral') }}

with src as (
    select practitioner_id
    from {{ ref('stg_ehr_integrations__practitioner') }}
    where practitioner_id is not null
)

select
    md5(practitioner_id)             as h_practitioner_hk,
    practitioner_id                  as practitioner_bk,
    current_date                     as load_date,
    'ehr_integrations.practitioner'  as record_source
from src
group by practitioner_id
