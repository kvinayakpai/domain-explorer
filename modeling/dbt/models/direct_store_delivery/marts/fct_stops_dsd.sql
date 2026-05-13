-- Fact: one row per stop. Carries on-time + sequence-drift + cases-delivered.
{{ config(materialized='table') }}

with s     as (select * from {{ ref('stg_direct_store_delivery__stop') }}),
     o     as (select * from {{ ref('stg_direct_store_delivery__dsd_order') }}),
     l     as (select * from {{ ref('stg_direct_store_delivery__dsd_order_line') }}),
     dr    as (select * from {{ ref('dim_route') }}),
     do_   as (select * from {{ ref('dim_outlet_dsd') }}),
     stop_agg as (
        select o.stop_id,
               sum(l.delivered_cases) as cases_delivered,
               sum(l.delivered_units) as units_delivered,
               sum(l.extended_amount_cents) as net_sales_cents
        from o
        left join l on l.order_id = o.order_id
        group by o.stop_id
     )

select
    s.stop_id,
    cast(strftime(s.route_day, '%Y%m%d') as integer)             as date_key,
    dr.route_sk,
    do_.outlet_sk,
    s.planned_sequence,
    s.actual_sequence,
    coalesce(s.actual_sequence - s.planned_sequence, 0)          as sequence_drift,
    s.planned_arrival,
    s.actual_arrival,
    s.arrival_minutes_delta                                       as on_time_window_minutes,
    case when abs(coalesce(s.arrival_minutes_delta, 999)) <= 15 then true else false end as is_on_time,
    s.dwell_minutes,
    s.is_skipped,
    s.is_completed,
    coalesce(stop_agg.cases_delivered, 0)                         as cases_delivered,
    coalesce(stop_agg.units_delivered, 0)                         as units_delivered,
    coalesce(stop_agg.net_sales_cents, 0)                         as net_sales_cents
from s
left join dr        on dr.route_id    = s.route_id
left join do_       on do_.outlet_id  = s.outlet_id
left join stop_agg  on stop_agg.stop_id = s.stop_id
