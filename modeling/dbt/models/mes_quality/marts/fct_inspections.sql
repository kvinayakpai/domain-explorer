-- Grain: one row per inspection (with defect counts rolled up).
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_mes_quality__inspections') }}),
     d as (
        select inspection_id,
               count(*) as defect_count,
               sum(case when severity = 'critical' then 1 else 0 end) as critical_count,
               sum(case when severity = 'major'    then 1 else 0 end) as major_count
        from {{ ref('stg_mes_quality__defects') }}
        group by inspection_id
     ),
     wo as (select work_order_id, line_id from {{ ref('stg_mes_quality__work_orders') }}),
     l  as (select * from {{ ref('dim_line') }})

select
    md5(i.inspection_id)                                  as inspection_key,
    i.inspection_id,
    i.work_order_id,
    md5(i.work_order_id)                                  as work_order_key,
    l.line_key,
    wo.line_id,
    cast({{ format_date('i.ts', '%Y%m%d') }} as integer)              as inspection_date_key,
    i.ts                                                   as inspected_at,
    i.result,
    i.inspector,
    i.method,
    coalesce(d.defect_count, 0)                            as defect_count,
    coalesce(d.critical_count, 0)                          as critical_defect_count,
    coalesce(d.major_count, 0)                             as major_defect_count,
    case when i.result = 'pass' then true else false end   as is_pass
from i
left join d  on d.inspection_id  = i.inspection_id
left join wo on wo.work_order_id = i.work_order_id
left join l  on l.line_id        = wo.line_id
