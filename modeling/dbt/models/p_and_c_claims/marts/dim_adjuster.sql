-- Adjuster dimension.
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_p_and_c_claims__adjusters') }})

select
    md5(adjuster_id)        as adjuster_key,
    adjuster_id,
    adjuster_name,
    specialty,
    license_state,
    experience_years,
    case
        when experience_years < 3  then 'junior'
        when experience_years < 10 then 'mid'
        else 'senior'
    end                      as seniority_band,
    is_active,
    current_date             as dim_loaded_at
from stg
