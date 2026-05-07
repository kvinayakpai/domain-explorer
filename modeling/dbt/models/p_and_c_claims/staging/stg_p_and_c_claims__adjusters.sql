-- Staging: claims adjuster master.
{{ config(materialized='view') }}

select
    cast(adjuster_id      as varchar) as adjuster_id,
    cast(name             as varchar) as adjuster_name,
    cast(specialty        as varchar) as specialty,
    cast(license_state    as varchar) as license_state,
    cast(experience_years as integer) as experience_years,
    cast(active           as boolean) as is_active
from {{ source('p_and_c_claims', 'adjusters') }}
