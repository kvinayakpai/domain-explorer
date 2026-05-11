-- Grain: one row per OMOP Condition Occurrence.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_real_world_evidence__condition_occurrence') }})

select
    c.condition_occurrence_id                                     as condition_occurrence_id,
    md5(cast(c.condition_occurrence_id as varchar))                as condition_key,
    md5(cast(c.person_id as varchar))                              as person_key,
    case when c.visit_occurrence_id is not null
         then md5(cast(c.visit_occurrence_id as varchar)) end       as visit_key,
    md5(cast(c.condition_concept_id as varchar))                   as condition_concept_key,
    cast({{ format_date('c.condition_start_date', '%Y%m%d') }} as integer)    as start_date_key,
    cast({{ format_date('c.condition_end_date', '%Y%m%d') }}   as integer)    as end_date_key,
    c.condition_concept_id,
    c.condition_source_value,
    c.condition_status_concept_id,
    c.condition_type_concept_id,
    c.stop_reason,
    c.provider_id,
    c.condition_start_date,
    c.condition_end_date,
    case
        when c.condition_end_date is not null
            then {{ dbt_utils.datediff('c.condition_start_date', 'c.condition_end_date', 'day') }}
    end                                                            as duration_days
from c
