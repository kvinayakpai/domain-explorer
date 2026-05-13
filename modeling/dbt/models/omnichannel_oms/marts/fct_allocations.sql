{{ config(materialized='table') }}

with a as (select * from {{ ref('stg_omnichannel_oms__allocations') }}),
     l as (select * from {{ ref('dim_location') }}),
     r as (select * from {{ ref('dim_sourcing_rule') }})

select
    a.allocation_id,
    a.order_line_id,
    cast({{ format_date('a.allocated_at', '%Y%m%d') }} as integer) as date_key,
    l.location_sk,
    r.rule_sk,
    a.allocated_quantity,
    a.estimated_cost_minor,
    a.estimated_cost_minor / 100.0 as estimated_cost_usd,
    a.estimated_ready_ts,
    a.estimated_delivery_ts,
    a.is_completed,
    a.is_reallocated,
    a.allocated_at
from a
left join l on l.location_id = a.location_id
left join r on r.rule_id     = a.rule_id
