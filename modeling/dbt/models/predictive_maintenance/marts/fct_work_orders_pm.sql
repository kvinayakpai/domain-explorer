-- Fact — one row per work order. Suffix `_pm` to avoid collision with any
-- other anchor's fct_work_orders.
{{ config(materialized='table') }}

with w as (select * from {{ ref('stg_predictive_maintenance__work_order') }}),
     a as (select * from {{ ref('dim_asset_pm') }}),
     f as (select failure_event_id, failure_mode_id from {{ ref('stg_predictive_maintenance__failure_event') }}),
     fm as (select * from {{ ref('dim_failure_mode') }})

select
    w.work_order_id,
    cast({{ format_date('w.scheduled_start', '%Y%m%d') }} as integer) as date_key,
    a.asset_sk,
    fm.failure_mode_sk,
    w.wo_type,
    w.wo_priority,
    w.is_predictive,
    w.is_emergency,
    w.scheduled_start,
    w.actual_start,
    w.actual_end,
    cast(w.repair_minutes as integer) as repair_minutes,
    w.labor_hours,
    w.parts_cost_usd,
    w.labor_cost_usd,
    w.total_cost_usd,
    w.status
from w
left join a  on a.asset_id        = w.asset_id
left join f  on f.failure_event_id = w.failure_event_id
left join fm on fm.failure_mode_id = f.failure_mode_id
