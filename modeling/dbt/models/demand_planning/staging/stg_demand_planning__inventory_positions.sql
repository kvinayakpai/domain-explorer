-- Staging: inventory positions.
{{ config(materialized='view') }}

select
    cast(position_id as varchar)   as position_id,
    cast(item_id     as varchar)   as item_id,
    cast(location_id as varchar)   as location_id,
    cast(on_hand     as integer)   as on_hand,
    cast(in_transit  as integer)   as in_transit,
    cast(reserved    as integer)   as reserved,
    cast(as_of       as timestamp) as as_of,
    cast(on_hand    as integer) + cast(in_transit as integer) - cast(reserved as integer)
                                    as available_position
from {{ source('demand_planning', 'inventory_positions') }}
