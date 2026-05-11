-- Staging: FHIR Organization.
{{ config(materialized='view') }}

select
    cast(organization_id   as varchar) as organization_id,
    cast(identifier_npi    as varchar) as identifier_npi,
    cast(type_code         as varchar) as type_code,
    cast(name              as varchar) as name,
    cast(telecom_phone     as varchar) as telecom_phone,
    cast(address_state     as varchar) as address_state,
    cast(active            as boolean) as active
from {{ source('ehr_integrations', 'organization') }}
