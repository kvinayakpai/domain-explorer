-- Fact — one row per supply plan item-location-cycle-scenario-period.
-- Joins to dim_item_sop, dim_location_sop, dim_sop_cycle, dim_scenario.
{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_sop_supply_chain_planning__supply_plans') }}),
     i as (select * from {{ ref('dim_item_sop') }}),
     l as (select * from {{ ref('dim_location_sop') }}),
     y as (select * from {{ ref('dim_sop_cycle') }}),
     n as (select * from {{ ref('dim_scenario') }})

select
    s.supply_plan_id,
    cast({{ format_date('s.period_start', '%Y%m%d') }} as integer) as date_key,
    i.item_sk,
    l.location_sk,
    s.source_location_id,
    y.cycle_sk,
    n.scenario_sk,
    s.supply_type,
    s.period_grain,
    s.planned_units,
    s.planned_value                                                as planned_value_usd,
    s.lead_time_days,
    s.status,
    s.published_at
from s
left join i on i.item_id     = s.item_id
left join l on l.location_id = s.location_id
left join y on y.cycle_id    = s.cycle_id
left join n on n.scenario_id = s.scenario_id
