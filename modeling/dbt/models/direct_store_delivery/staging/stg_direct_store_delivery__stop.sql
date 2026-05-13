{{ config(materialized='view') }}

select
    cast(stop_id            as varchar)  as stop_id,
    cast(route_id           as varchar)  as route_id,
    cast(route_day          as date)     as route_day,
    cast(outlet_id          as varchar)  as outlet_id,
    cast(gln                as varchar)  as gln,
    cast(planned_sequence   as smallint) as planned_sequence,
    cast(actual_sequence    as smallint) as actual_sequence,
    cast(planned_arrival    as timestamp) as planned_arrival,
    cast(actual_arrival     as timestamp) as actual_arrival,
    cast(planned_departure  as timestamp) as planned_departure,
    cast(actual_departure   as timestamp) as actual_departure,
    cast(dwell_minutes      as integer)  as dwell_minutes,
    cast(status             as varchar)  as status,
    cast(skip_reason        as varchar)  as skip_reason,
    cast(lat                as double)   as lat,
    cast(lng                as double)   as lng,
    cast(presell_flag       as boolean)  as presell_flag,
    -- Derived columns useful for facts
    case when actual_arrival is not null and planned_arrival is not null
         then cast((extract(epoch from (actual_arrival - planned_arrival)) / 60) as integer)
         else null end                                         as arrival_minutes_delta,
    case when status = 'completed' then true else false end    as is_completed,
    case when status = 'skipped'   then true else false end    as is_skipped
from {{ source('direct_store_delivery', 'stop') }}
