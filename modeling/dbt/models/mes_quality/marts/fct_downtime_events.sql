-- Grain: one row per downtime event.
{{ config(materialized='table') }}

with d as (select * from {{ ref('stg_mes_quality__downtime_events') }}),
     e as (select * from {{ ref('dim_equipment') }})

select
    md5(d.downtime_id)                                       as downtime_key,
    d.downtime_id,
    d.equipment_id,
    e.equipment_key,
    e.line_key,
    cast({{ format_date('d.started_at', '%Y%m%d') }} as integer)         as start_date_key,
    cast({{ format_date('d.ended_at', '%Y%m%d') }} as integer)         as end_date_key,
    d.started_at,
    d.ended_at,
    d.category,
    d.duration_minutes,
    case when d.category = 'planned_maintenance' then true else false end as is_planned
from d
left join e on e.equipment_id = d.equipment_id
