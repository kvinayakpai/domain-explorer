-- Grain: one row per reservation. Surfaces property + room type + channel keys
-- and rolls up ancillary spend + cancellation flags.
{{ config(materialized='table') }}

with hub_r as (select * from {{ ref('int_hotel_revenue_management__hub_reservation') }}),
     sat   as (select * from {{ ref('int_hotel_revenue_management__sat_reservation') }}),
     l     as (select * from {{ ref('int_hotel_revenue_management__link_reservation_property_room') }}),
     anc as (
         select
             reservation_id,
             count(*)                       as ancillary_count,
             coalesce(sum(amount), 0.0)     as ancillary_amount
         from {{ ref('stg_hotel_revenue_management__ancillaries') }}
         group by reservation_id
     ),
     cxl as (
         select
             reservation_id,
             min(cancelled_at)              as cancelled_at,
             max(fee_amount)                as cancellation_fee,
             min(reason)                    as cancellation_reason
         from {{ ref('stg_hotel_revenue_management__cancellations') }}
         group by reservation_id
     )

select
    h.h_reservation_hk                                  as reservation_key,
    h.reservation_bk                                    as reservation_id,
    l.h_property_hk                                     as property_key,
    l.h_room_type_hk                                    as room_type_key,
    md5(s.channel_id)                                   as channel_key,
    s.channel_id,
    s.guest_id,
    md5(s.guest_id)                                     as guest_key,
    s.rate_plan_id,
    md5(s.rate_plan_id)                                 as rate_plan_key,
    s.reservation_status,
    s.arrival_date,
    cast({{ format_date('s.arrival_date', '%Y%m%d') }} as integer) as arrival_date_key,
    s.departure_date,
    s.nights,
    s.adr,
    s.total_amount,
    s.lead_time_days,
    coalesce(anc.ancillary_count, 0)                    as ancillary_count,
    coalesce(anc.ancillary_amount, 0.0)                 as ancillary_amount,
    s.total_amount + coalesce(anc.ancillary_amount, 0.0) as total_revenue,
    cxl.cancelled_at,
    cxl.cancellation_fee,
    cxl.cancellation_reason,
    case when cxl.cancelled_at is not null then true else false end as is_cancelled
from hub_r h
join sat s on s.h_reservation_hk = h.h_reservation_hk
left join l   on l.h_reservation_hk = h.h_reservation_hk
left join anc on anc.reservation_id = h.reservation_bk
left join cxl on cxl.reservation_id = h.reservation_bk
