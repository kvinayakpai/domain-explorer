{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_omnichannel_oms__shipments') }}),
     a as (select * from {{ ref('stg_omnichannel_oms__allocations') }}),
     l as (select * from {{ ref('dim_location') }}),
     c as (select * from {{ ref('dim_carrier') }})

select
    s.shipment_id,
    s.allocation_id,
    cast({{ format_date('s.shipped_at', '%Y%m%d') }} as integer) as date_key,
    c.carrier_sk,
    l.location_sk                                                 as ship_from_location_sk,
    s.service_level,
    s.weight_grams,
    s.cost_minor,
    s.cost_minor / 100.0                                          as cost_usd,
    s.shipped_at,
    s.delivered_at,
    s.transit_hours,
    case when s.delivered_at is not null
              and a.estimated_delivery_ts is not null
              and s.delivered_at <= a.estimated_delivery_ts
         then true else false end as is_on_time,
    s.is_delivered
from s
left join a on a.allocation_id     = s.allocation_id
left join c on c.carrier            = s.carrier
left join l on l.location_id        = s.ship_from_location_id
