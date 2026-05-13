{{ config(materialized='view') }}

select
    cast(work_order_id                  as varchar)    as work_order_id,
    cast(asset_id                       as varchar)    as asset_id,
    cast(wo_type                        as varchar)    as wo_type,
    cast(wo_priority                    as smallint)   as wo_priority,
    cast(triggered_by_prediction_id     as varchar)    as triggered_by_prediction_id,
    cast(scheduled_start                as timestamp)  as scheduled_start,
    cast(actual_start                   as timestamp)  as actual_start,
    cast(actual_end                     as timestamp)  as actual_end,
    cast(labor_hours                    as double)     as labor_hours,
    cast(parts_cost_usd                 as double)     as parts_cost_usd,
    cast(labor_cost_usd                 as double)     as labor_cost_usd,
    cast(status                         as varchar)    as status,
    cast(failure_event_id               as varchar)    as failure_event_id,
    cast(crew_id                        as varchar)    as crew_id,
    case when wo_type = 'predictive' then true else false end as is_predictive,
    case when wo_type = 'preventive' then true else false end as is_preventive,
    case when wo_type = 'corrective' then true else false end as is_corrective,
    case when wo_type = 'emergency'  then true else false end as is_emergency,
    case when wo_type in ('preventive','predictive','inspection') then true else false end as is_planned,
    case
        when actual_start is not null and actual_end is not null
            then {{ dbt_utils.datediff('actual_start', 'actual_end', 'minute') }}
    end as repair_minutes,
    (coalesce(parts_cost_usd, 0) + coalesce(labor_cost_usd, 0)) as total_cost_usd
from {{ source('predictive_maintenance', 'work_order') }}
