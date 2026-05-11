-- Grain: one row per work order.
{{ config(materialized='table') }}

with wo as (select * from {{ ref('stg_mes_quality__work_orders') }}),
     l  as (select * from {{ ref('dim_line') }}),
     p  as (select * from {{ ref('dim_product_mes_quality') }})

select
    md5(wo.work_order_id)                                        as work_order_key,
    wo.work_order_id,
    l.line_key,
    wo.line_id,
    p.product_key,
    wo.product_code,
    wo.qty_planned,
    wo.qty_produced,
    case when coalesce(wo.qty_planned, 0) = 0 then null
         else wo.qty_produced::double / wo.qty_planned end        as completion_ratio,
    cast({{ format_date('wo.started_at', '%Y%m%d') }} as integer)             as started_date_key,
    cast({{ format_date('wo.ended_at', '%Y%m%d') }} as integer)             as ended_date_key,
    wo.started_at,
    wo.ended_at,
    case when wo.ended_at is not null and wo.started_at is not null
         then {{ dbt_utils.datediff('wo.started_at', 'wo.ended_at', 'minute') }}
         end                                                       as duration_minutes,
    wo.status
from wo
left join l on l.line_id      = wo.line_id
left join p on p.product_id   = wo.product_code
