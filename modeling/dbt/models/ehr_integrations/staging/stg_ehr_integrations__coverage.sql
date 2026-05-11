-- Staging: FHIR Coverage (insurance plan).
{{ config(materialized='view') }}

select
    cast(coverage_id      as varchar) as coverage_id,
    cast(patient_id       as varchar) as patient_id,
    cast(status           as varchar) as status,
    cast(type_code        as varchar) as type_code,
    cast(subscriber_id    as varchar) as subscriber_id,
    cast(payor_org_id     as varchar) as payor_org_id,
    cast(relationship_code as varchar) as relationship_code,
    cast(period_start     as date)    as period_start,
    cast(plan_name        as varchar) as plan_name,
    cast(network          as varchar) as network
from {{ source('ehr_integrations', 'coverage') }}
