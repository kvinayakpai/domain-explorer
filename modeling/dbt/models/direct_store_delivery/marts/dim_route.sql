-- Route dimension (Type-2 ready). No suffix needed — route is DSD-unique.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_direct_store_delivery__hub_route') }}),
     stg as (select * from {{ ref('stg_direct_store_delivery__route') }})

select
    h.h_route_hk            as route_sk,
    h.route_bk              as route_id,
    s.branch_id,
    s.route_code,
    s.route_type,
    s.service_days,
    s.vehicle_class,
    s.planned_stops,
    s.planned_miles,
    s.planned_duration_min,
    s.status,
    s.created_at            as valid_from,
    cast(null as timestamp) as valid_to,
    true                    as is_current
from hub h
left join stg s on s.route_id = h.route_bk
