-- Line dimension; FK to dim_plant via plant_key.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_mes_quality__hub_line') }}),
     stg as (select * from {{ ref('stg_mes_quality__lines') }}),
     p   as (select * from {{ ref('dim_plant') }})

select
    h.h_line_hk           as line_key,
    h.line_bk             as line_id,
    p.plant_key,
    s.plant_id,
    s.line_type,
    s.ideal_cycle_seconds,
    s.shifts_per_day,
    h.load_date           as dim_loaded_at,
    true                  as is_current
from hub h
left join stg s on s.line_id  = h.line_bk
left join p   on p.plant_id   = s.plant_id
