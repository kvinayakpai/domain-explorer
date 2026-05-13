-- Grain: one row per (property, stay_date). Daily revenue, occupancy and yield
-- combining daily_inventory (availability), daily_pricing (rate, yield score),
-- and reservation revenue attributed by arrival_date.
{{ config(materialized='table') }}

with rt   as (select * from {{ ref('stg_hotel_revenue_management__room_types') }}),
     inv  as (select * from {{ ref('stg_hotel_revenue_management__daily_inventory') }}),
     dp   as (select * from {{ ref('stg_hotel_revenue_management__daily_pricing') }}),
     res  as (select * from {{ ref('stg_hotel_revenue_management__reservations') }}),
     anc  as (
         select reservation_id, coalesce(sum(amount), 0.0) as ancillary_amount
         from {{ ref('stg_hotel_revenue_management__ancillaries') }}
         group by reservation_id
     ),
     daily_inv as (
         select
             rt.property_id,
             inv.stay_date,
             sum(inv.available_rooms)    as available_rooms,
             sum(inv.sold_rooms)         as sold_rooms,
             sum(inv.out_of_order_rooms) as out_of_order_rooms,
             avg(inv.occupancy_pct)      as avg_occupancy_pct
         from inv
         join rt on rt.room_type_id = inv.room_type_id
         group by rt.property_id, inv.stay_date
     ),
     daily_price as (
         select
             rt.property_id,
             dp.stay_date,
             avg(dp.rate)        as avg_rate,
             max(dp.yield_score) as max_yield_score
         from dp
         join rt on rt.room_type_id = dp.room_type_id
         group by rt.property_id, dp.stay_date
     ),
     daily_res as (
         select
             rt.property_id,
             cast(res.arrival_date as date) as stay_date,
             count(*)                       as arrivals,
             sum(res.nights)                as room_nights,
             sum(res.total_amount)          as room_revenue,
             sum(coalesce(a.ancillary_amount, 0.0)) as ancillary_revenue
         from res
         join rt on rt.room_type_id = res.room_type_id
         left join anc a on a.reservation_id = res.reservation_id
         group by rt.property_id, cast(res.arrival_date as date)
     )

select
    md5(d.property_id || '|' || cast(d.stay_date as varchar)) as daily_revenue_key,
    d.property_id,
    md5(d.property_id)                                        as property_key,
    d.stay_date,
    cast({{ format_date('d.stay_date', '%Y%m%d') }} as integer)          as stay_date_key,
    d.available_rooms,
    d.sold_rooms,
    d.out_of_order_rooms,
    d.avg_occupancy_pct,
    p.avg_rate                                                as adr_published,
    p.max_yield_score,
    coalesce(r.arrivals, 0)                                   as arrivals,
    coalesce(r.room_nights, 0)                                as room_nights,
    coalesce(r.room_revenue, 0.0)                             as room_revenue,
    coalesce(r.ancillary_revenue, 0.0)                        as ancillary_revenue,
    coalesce(r.room_revenue, 0.0)
      + coalesce(r.ancillary_revenue, 0.0)                    as total_revenue,
    case
        when d.available_rooms > 0
            then coalesce(r.room_revenue, 0.0) / d.available_rooms
    end                                                       as revpar,
    case
        when d.sold_rooms > 0
            then coalesce(r.room_revenue, 0.0) / d.sold_rooms
    end                                                       as adr_realized
from daily_inv d
left join daily_price p on p.property_id = d.property_id and p.stay_date = d.stay_date
left join daily_res   r on r.property_id = d.property_id and r.stay_date = d.stay_date
