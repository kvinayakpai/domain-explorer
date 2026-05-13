{{ config(materialized='view') }}

select
    cast(route_id             as varchar)  as route_id,
    cast(branch_id            as varchar)  as branch_id,
    cast(route_code           as varchar)  as route_code,
    cast(route_type           as varchar)  as route_type,
    cast(service_days         as varchar)  as service_days,
    cast(planned_stops        as smallint) as planned_stops,
    cast(planned_miles        as double)   as planned_miles,
    cast(planned_duration_min as integer)  as planned_duration_min,
    cast(vehicle_class        as varchar)  as vehicle_class,
    cast(status               as varchar)  as status,
    cast(created_at           as timestamp) as created_at,
    cast(effective_from       as date)     as effective_from,
    cast(effective_to         as date)     as effective_to
from {{ source('direct_store_delivery', 'route') }}
