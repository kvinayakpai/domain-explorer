-- Grain: one row per OMOP Measurement (LOINC labs/vitals).
{{ config(materialized='table') }}

with m as (select * from {{ ref('stg_real_world_evidence__measurement') }})

select
    m.measurement_id                                              as measurement_id,
    md5(cast(m.measurement_id as varchar))                         as measurement_key,
    md5(cast(m.person_id as varchar))                              as person_key,
    case when m.visit_occurrence_id is not null
         then md5(cast(m.visit_occurrence_id as varchar)) end       as visit_key,
    md5(cast(m.measurement_concept_id as varchar))                 as measurement_concept_key,
    cast({{ format_date('m.measurement_date', '%Y%m%d') }} as integer)        as measurement_date_key,
    m.measurement_concept_id,
    m.measurement_source_value,
    m.measurement_type_concept_id,
    m.unit_concept_id,
    m.value_as_number,
    m.value_as_concept_id,
    m.range_low,
    m.range_high,
    m.is_out_of_range,
    m.measurement_date,
    m.measurement_datetime,
    m.provider_id
from m
