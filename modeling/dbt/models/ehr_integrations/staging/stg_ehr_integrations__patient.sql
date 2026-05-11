-- Staging: FHIR Patient (USCDI core demographics).
{{ config(materialized='view') }}

select
    cast(patient_id              as varchar) as patient_id,
    cast(identifier_mrn          as varchar) as identifier_mrn,
    cast(family_name             as varchar) as family_name,
    cast(given_names             as varchar) as given_names,
    cast(gender                  as varchar) as gender,
    cast(birth_date              as date)    as birth_date,
    cast(marital_status_code     as varchar) as marital_status_code,
    cast(race_code               as varchar) as race_code,
    cast(ethnicity_code          as varchar) as ethnicity_code,
    cast(address_state           as varchar) as address_state,
    cast(address_country         as varchar) as address_country,
    cast(managing_organization_id as varchar) as managing_organization_id,
    cast(language_code           as varchar) as language_code,
    cast({{ dbt_utils.datediff('birth_date', 'current_date', 'year') }} as integer) as age_years
from {{ source('ehr_integrations', 'patient') }}
