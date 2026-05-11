-- Staging: FHIR Practitioner.
{{ config(materialized='view') }}

select
    cast(practitioner_id            as varchar) as practitioner_id,
    cast(npi                        as varchar) as npi,
    cast(family_name                as varchar) as family_name,
    cast(given_names                as varchar) as given_names,
    cast(gender                     as varchar) as gender,
    cast(qualification_code         as varchar) as qualification_code,
    cast(qualification_issuer_org_id as varchar) as qualification_issuer_org_id,
    cast(active                     as boolean) as active
from {{ source('ehr_integrations', 'practitioner') }}
