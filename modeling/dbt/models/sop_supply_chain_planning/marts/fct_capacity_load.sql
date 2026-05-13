-- Fact — capacity vs planned load per resource-period. Drives Capacity Utilization %.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_sop_supply_chain_planning__capacity') }}),
     l as (select * from {{ ref('dim_location_sop') }})

select
    row_number() over (order by capacity_id)                              as capacity_load_id,
    cast({{ format_date('c.period_start', '%Y%m%d') }} as integer)         as date_key,
    l.location_sk,
    c.resource_id,
    c.resource_type,
    c.available_hours,
    c.planned_load_hours,
    c.utilization_pct,
    c.changeover_hours,
    case when c.utilization_pct >= 95 then true else false end             as is_constrained,
    c.status
from c
left join l on l.location_id = c.location_id
