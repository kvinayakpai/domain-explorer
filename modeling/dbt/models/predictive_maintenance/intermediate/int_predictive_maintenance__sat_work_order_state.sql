-- Vault satellite carrying Work Order lifecycle state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_predictive_maintenance__work_order') }})

select
    md5(work_order_id)                                                              as h_work_order_hk,
    scheduled_start                                                                 as load_ts,
    md5(coalesce(wo_type,'') || '|' || cast(coalesce(wo_priority, 0) as varchar)
        || '|' || coalesce(status,'') || '|' || cast(coalesce(labor_hours, 0) as varchar)
        || '|' || cast(coalesce(parts_cost_usd, 0) as varchar))                     as hashdiff,
    wo_type,
    wo_priority,
    scheduled_start,
    actual_start,
    actual_end,
    labor_hours,
    parts_cost_usd,
    labor_cost_usd,
    status,
    crew_id,
    'predictive_maintenance.work_order'                                              as record_source
from src
