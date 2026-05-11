-- Staging: OMOP Observation Period.
{{ config(materialized='view') }}

select
    cast(observation_period_id        as bigint) as observation_period_id,
    cast(person_id                    as bigint) as person_id,
    cast(observation_period_start_date as date)  as observation_period_start_date,
    cast(observation_period_end_date  as date)   as observation_period_end_date,
    cast(period_type_concept_id       as bigint) as period_type_concept_id,
    cast({{ dbt_utils.datediff('observation_period_start_date', 'observation_period_end_date', 'day') }} as integer)
                                                  as observation_period_days
from {{ source('real_world_evidence', 'observation_period') }}
