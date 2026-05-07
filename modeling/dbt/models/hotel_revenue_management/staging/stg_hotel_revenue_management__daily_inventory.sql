-- Staging: daily room-type availability.
{{ config(materialized='view') }}

select
    cast(inv_id       as varchar) as inv_id,
    cast(room_type_id as varchar) as room_type_id,
    cast(stay_date    as date)    as stay_date,
    cast(available    as integer) as available_rooms,
    cast(sold         as integer) as sold_rooms,
    cast(out_of_order as integer) as out_of_order_rooms,
    case
        when (cast(available as integer) + cast(sold as integer)) > 0
            then cast(sold as integer)::double
                 / (cast(available as integer) + cast(sold as integer))
    end                              as occupancy_pct
from {{ source('hotel_revenue_management', 'daily_inventory') }}
