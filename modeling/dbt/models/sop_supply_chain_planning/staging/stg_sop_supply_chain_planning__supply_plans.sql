{{ config(materialized='view') }}

select
    cast(supply_plan_id     as bigint)   as supply_plan_id,
    cast(item_id            as varchar)  as item_id,
    cast(location_id        as varchar)  as location_id,
    cast(source_location_id as varchar)  as source_location_id,
    cast(supply_type        as varchar)  as supply_type,
    cast(cycle_id           as varchar)  as cycle_id,
    cast(scenario_id        as varchar)  as scenario_id,
    cast(period_start       as date)     as period_start,
    cast(period_grain       as varchar)  as period_grain,
    cast(planned_units      as double)   as planned_units,
    cast(planned_value      as double)   as planned_value,
    cast(lead_time_days     as smallint) as lead_time_days,
    cast(status             as varchar)  as status,
    cast(published_at       as timestamp) as published_at
from {{ source('sop_supply_chain_planning', 'supply_plan') }}
