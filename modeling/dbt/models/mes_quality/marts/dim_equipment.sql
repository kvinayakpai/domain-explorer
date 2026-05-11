-- Equipment dimension; FK to dim_line via line_key.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_mes_quality__hub_equipment') }}),
     sat as (select * from {{ ref('int_mes_quality__sat_equipment_descriptive') }}),
     stg as (select * from {{ ref('stg_mes_quality__equipment') }}),
     l   as (select * from {{ ref('dim_line') }})

select
    h.h_equipment_hk        as equipment_key,
    h.equipment_bk          as equipment_id,
    l.line_key,
    stg.line_id,
    sat.kind,
    sat.vendor,
    sat.install_year,
    sat.criticality,
    h.load_date             as dim_loaded_at,
    true                    as is_current
from hub h
left join sat on sat.h_equipment_hk = h.h_equipment_hk
left join stg on stg.equipment_id   = h.equipment_bk
left join l   on l.line_id           = stg.line_id
