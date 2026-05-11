-- Staging: downtime events.
{{ config(materialized='view') }}

select
    cast(downtime_id      as varchar)   as downtime_id,
    cast(equipment_id     as varchar)   as equipment_id,
    cast(started_at       as timestamp) as started_at,
    cast(ended_at         as timestamp) as ended_at,
    cast(category         as varchar)   as category,
    cast(duration_minutes as double)    as duration_minutes
from {{ source('mes_quality', 'downtime_events') }}
