{{ config(materialized='view') }}

select
    cast(scenario_id                as varchar)  as scenario_id,
    cast(cycle_id                   as varchar)  as cycle_id,
    cast(scenario_name              as varchar)  as scenario_name,
    cast(scenario_type              as varchar)  as scenario_type,
    cast(description                as varchar)  as description,
    cast(created_by                 as varchar)  as created_by,
    cast(created_at                 as timestamp) as created_at,
    cast(published_at               as timestamp) as published_at,
    cast(status                     as varchar)  as status,
    cast(revenue_impact_usd         as double)   as revenue_impact_usd,
    cast(working_capital_impact_usd as double)   as working_capital_impact_usd,
    cast(service_level_impact_pct   as double)   as service_level_impact_pct
from {{ source('sop_supply_chain_planning', 'scenario') }}
