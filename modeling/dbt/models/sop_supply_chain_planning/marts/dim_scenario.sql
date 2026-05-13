-- Scenario dimension — one row per what-if planning scenario.
{{ config(materialized='table') }}

select
    row_number() over (order by scenario_id)   as scenario_sk,
    scenario_id,
    cycle_id,
    scenario_name,
    scenario_type,
    status,
    revenue_impact_usd,
    working_capital_impact_usd,
    service_level_impact_pct,
    created_at,
    published_at
from {{ ref('stg_sop_supply_chain_planning__scenarios') }}
