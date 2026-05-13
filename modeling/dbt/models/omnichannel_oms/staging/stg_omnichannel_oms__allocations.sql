{{ config(materialized='view') }}

select
    cast(allocation_id          as varchar)    as allocation_id,
    cast(order_line_id          as varchar)    as order_line_id,
    cast(location_id            as varchar)    as location_id,
    cast(rule_id                as varchar)    as rule_id,
    cast(allocated_quantity     as integer)    as allocated_quantity,
    cast(estimated_cost_minor   as bigint)     as estimated_cost_minor,
    cast(estimated_ready_ts     as timestamp)  as estimated_ready_ts,
    cast(estimated_delivery_ts  as timestamp)  as estimated_delivery_ts,
    cast(status                 as varchar)    as status,
    cast(allocated_at           as timestamp)  as allocated_at,
    case when status = 'completed'    then true else false end as is_completed,
    case when status = 'reallocated'  then true else false end as is_reallocated
from {{ source('omnichannel_oms', 'allocation') }}
