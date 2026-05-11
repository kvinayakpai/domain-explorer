-- Staging: light typing on smart_metering.field_order.
{{ config(materialized='view') }}

select
    cast(field_order_id as varchar)   as field_order_id,
    cast(meter_id       as varchar)   as meter_id,
    cast(order_type     as varchar)   as order_type,
    cast(priority       as varchar)   as priority,
    cast(opened_at      as timestamp) as opened_at,
    cast(scheduled_at   as timestamp) as scheduled_at,
    cast(completed_at   as timestamp) as completed_at,
    cast(technician_id  as varchar)   as technician_id,
    cast(status         as varchar)   as status,
    case
        when completed_at is not null
            then {{ dbt_utils.datediff('opened_at', 'completed_at', 'hour') }}
    end as resolution_hours
from {{ source('smart_metering', 'field_order') }}
