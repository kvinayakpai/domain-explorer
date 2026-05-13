{{ config(materialized='view') }}

select
    cast(plan_id            as varchar)    as plan_id,
    cast(asset_id           as varchar)    as asset_id,
    cast(plan_type          as varchar)    as plan_type,
    cast(interval_value     as integer)    as interval_value,
    cast(interval_unit      as varchar)    as interval_unit,
    cast(trigger_condition  as varchar)    as trigger_condition,
    cast(job_plan_template  as varchar)    as job_plan_template,
    cast(active             as boolean)    as active,
    cast(created_at         as timestamp)  as created_at
from {{ source('predictive_maintenance', 'maintenance_plan') }}
