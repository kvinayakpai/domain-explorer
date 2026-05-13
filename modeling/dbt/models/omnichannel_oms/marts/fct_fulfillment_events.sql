{{ config(materialized='table') }}

with e as (select * from {{ ref('stg_omnichannel_oms__fulfillment_events') }}),
     l as (select * from {{ ref('dim_location') }})

select
    e.event_id,
    e.allocation_id,
    e.order_line_id,
    cast({{ format_date('e.occurred_at', '%Y%m%d') }} as integer) as date_key,
    l.location_sk,
    e.event_type,
    e.actor_role,
    e.occurred_at
from e
left join l on l.location_id = e.location_id
