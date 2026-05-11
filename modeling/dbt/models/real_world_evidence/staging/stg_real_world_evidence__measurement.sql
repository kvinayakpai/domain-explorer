-- Staging: OMOP Measurement.
{{ config(materialized='view') }}

select
    cast(measurement_id              as bigint)    as measurement_id,
    cast(person_id                   as bigint)    as person_id,
    cast(measurement_concept_id      as bigint)    as measurement_concept_id,
    cast(measurement_date            as date)      as measurement_date,
    cast(measurement_datetime        as timestamp) as measurement_datetime,
    cast(measurement_type_concept_id as bigint)    as measurement_type_concept_id,
    cast(operator_concept_id         as bigint)    as operator_concept_id,
    cast(value_as_number             as double)    as value_as_number,
    cast(value_as_concept_id         as bigint)    as value_as_concept_id,
    cast(unit_concept_id             as bigint)    as unit_concept_id,
    cast(range_low                   as double)    as range_low,
    cast(range_high                  as double)    as range_high,
    cast(provider_id                 as bigint)    as provider_id,
    cast(visit_occurrence_id         as bigint)    as visit_occurrence_id,
    cast(measurement_source_value    as varchar)   as measurement_source_value,
    case
        when cast(value_as_number as double) < cast(range_low as double) then true
        when cast(value_as_number as double) > cast(range_high as double) then true
        else false
    end as is_out_of_range
from {{ source('real_world_evidence', 'measurement') }}
