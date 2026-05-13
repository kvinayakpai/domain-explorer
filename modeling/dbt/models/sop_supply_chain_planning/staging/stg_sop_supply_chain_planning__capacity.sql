{{ config(materialized='view') }}

select
    cast(capacity_id        as varchar)  as capacity_id,
    cast(location_id        as varchar)  as location_id,
    cast(resource_id        as varchar)  as resource_id,
    cast(resource_type      as varchar)  as resource_type,
    cast(period_start       as date)     as period_start,
    cast(period_grain       as varchar)  as period_grain,
    cast(available_hours    as double)   as available_hours,
    cast(planned_load_hours as double)   as planned_load_hours,
    cast(utilization_pct    as double)   as utilization_pct,
    cast(changeover_hours   as double)   as changeover_hours,
    cast(status             as varchar)  as status
from {{ source('sop_supply_chain_planning', 'capacity') }}
