-- Staging: room types per property.
{{ config(materialized='view') }}

select
    cast(room_type_id  as varchar) as room_type_id,
    cast(property_id   as varchar) as property_id,
    cast(name          as varchar) as room_type_name,
    cast(max_occupancy as integer) as max_occupancy,
    cast(view          as varchar) as room_view,
    cast(size_sqm      as integer) as size_sqm
from {{ source('hotel_revenue_management', 'room_types') }}
