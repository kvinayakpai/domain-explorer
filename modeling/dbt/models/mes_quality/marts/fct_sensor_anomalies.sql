-- Grain: one row per sensor anomaly reading. Filters non-anomalies for compactness.
{{ config(materialized='table') }}

with s as (
    select * from {{ ref('stg_mes_quality__sensor_readings') }}
    where anomaly = true
),
e as (select * from {{ ref('dim_equipment') }})

select
    md5(s.reading_id)                                  as anomaly_key,
    s.reading_id,
    s.equipment_id,
    e.equipment_key,
    e.line_key,
    s.metric,
    s.value,
    cast({{ format_date('s.ts', '%Y%m%d') }} as integer)           as anomaly_date_key,
    s.ts                                                as anomaly_ts
from s
left join e on e.equipment_id = s.equipment_id
