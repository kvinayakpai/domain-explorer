-- Staging: OMOP Person.
{{ config(materialized='view') }}

select
    cast(person_id              as bigint)  as person_id,
    cast(gender_concept_id      as bigint)  as gender_concept_id,
    cast(year_of_birth          as integer) as year_of_birth,
    cast(month_of_birth         as integer) as month_of_birth,
    cast(day_of_birth           as integer) as day_of_birth,
    cast(race_concept_id        as bigint)  as race_concept_id,
    cast(ethnicity_concept_id   as bigint)  as ethnicity_concept_id,
    cast(location_id            as bigint)  as location_id,
    cast(provider_id            as bigint)  as provider_id,
    cast(care_site_id           as bigint)  as care_site_id,
    cast(person_source_value    as varchar) as person_source_value,
    case
        when extract(year from current_date) - cast(year_of_birth as integer) < 18 then 'pediatric'
        when extract(year from current_date) - cast(year_of_birth as integer) < 65 then 'adult'
        else 'geriatric'
    end as age_group
from {{ source('real_world_evidence', 'person') }}
