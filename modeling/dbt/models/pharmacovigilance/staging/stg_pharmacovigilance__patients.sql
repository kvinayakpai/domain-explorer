-- Staging: PV patient demographics.
{{ config(materialized='view') }}

select
    cast(patient_id        as varchar) as patient_id,
    cast(age               as integer) as age,
    cast(sex               as varchar) as sex,
    cast(weight_kg         as double)  as weight_kg,
    upper(country)                     as country,
    cast(pregnancy_status  as varchar) as pregnancy_status,
    case
        when cast(age as integer) < 18 then 'pediatric'
        when cast(age as integer) < 65 then 'adult'
        else 'geriatric'
    end as age_group
from {{ source('pharmacovigilance', 'patients') }}
