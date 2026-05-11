-- Staging: production lines.
{{ config(materialized='view') }}

select
    cast(line_id              as varchar) as line_id,
    cast(plant_id             as varchar) as plant_id,
    cast(line_type            as varchar) as line_type,
    cast(ideal_cycle_seconds  as double)  as ideal_cycle_seconds,
    cast(shifts_per_day       as integer) as shifts_per_day
from {{ source('mes_quality', 'lines') }}
