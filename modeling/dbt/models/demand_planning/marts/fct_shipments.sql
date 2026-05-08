-- Grain: one row per outbound shipment line. Surfaces conformed item /
-- location keys and computed transit / on-time signals.
{{ config(materialized='table') }}

with s as (select * from {{ ref('stg_demand_planning__shipments') }}),
     hub_i as (select * from {{ ref('int_demand_planning__hub_item') }}),
     hub_l as (select * from {{ ref('int_demand_planning__hub_location') }}),
     hub_c as (select * from {{ ref('int_demand_planning__hub_customer') }})

select
    md5(s.shipment_id)                                       as shipment_key,
    s.shipment_id,
    s.item_id,
    i.h_item_hk                                              as item_key,
    s.from_location_id,
    l.h_location_hk                                          as from_location_key,
    s.customer_id,
    c.h_customer_hk                                          as customer_key,
    s.quantity,
    s.carrier,
    s.shipped_at,
    s.delivered_at,
    cast(strftime(s.shipped_at,   '%Y%m%d') as integer)       as shipped_date_key,
    cast(strftime(s.delivered_at, '%Y%m%d') as integer)       as delivered_date_key,
    s.transit_hours,
    s.on_time,
    case
        when s.delivered_at is null                  then 'in_transit'
        when s.on_time = true                        then 'on_time'
        else 'late'
    end                                                       as delivery_status,
    case
        when s.transit_hours is null                 then 'unknown'
        when s.transit_hours <= 24                   then 'next_day'
        when s.transit_hours <= 72                   then 'three_day'
        when s.transit_hours <= 168                  then 'one_week'
        else 'over_one_week'
    end                                                       as transit_band
from s
left join hub_i i on i.item_bk     = s.item_id
left join hub_l l on l.location_bk = s.from_location_id
left join hub_c c on c.customer_bk = s.customer_id
