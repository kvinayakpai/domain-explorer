-- Staging: PV reporters (HCPs, consumers, regulators).
{{ config(materialized='view') }}

select
    cast(reporter_id  as varchar) as reporter_id,
    cast(name         as varchar) as name,
    cast(role         as varchar) as role,
    upper(country)                as country,
    cast(qualified_hcp as boolean) as qualified_hcp
from {{ source('pharmacovigilance', 'reporters') }}
