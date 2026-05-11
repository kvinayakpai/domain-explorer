-- Grain: one row per scrap event.
{{ config(materialized='table') }}

with s  as (select * from {{ ref('stg_mes_quality__scrap_events') }}),
     wo as (select work_order_id, line_id from {{ ref('stg_mes_quality__work_orders') }}),
     l  as (select * from {{ ref('dim_line') }})

select
    md5(s.scrap_id)                                       as scrap_key,
    s.scrap_id,
    s.work_order_id,
    md5(s.work_order_id)                                  as work_order_key,
    l.line_key,
    wo.line_id,
    s.qty,
    s.reason_code,
    s.cost,
    cast({{ format_date('s.ts', '%Y%m%d') }} as integer)              as scrap_date_key,
    s.ts                                                   as scrapped_at
from s
left join wo on wo.work_order_id = s.work_order_id
left join l  on l.line_id        = wo.line_id
