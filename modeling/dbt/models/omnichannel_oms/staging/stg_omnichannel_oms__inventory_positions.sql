{{ config(materialized='view') }}

select
    cast(position_id              as varchar)    as position_id,
    cast(location_id              as varchar)    as location_id,
    cast(product_id               as varchar)    as product_id,
    cast(on_hand_units            as integer)    as on_hand_units,
    cast(allocated_units          as integer)    as allocated_units,
    cast(in_transit_units         as integer)    as in_transit_units,
    cast(reserved_safety_units    as integer)    as reserved_safety_units,
    cast(atp_units                as integer)    as atp_units,
    cast(source_system            as varchar)    as source_system,
    cast(as_of_ts                 as timestamp)  as as_of_ts,
    cast(refresh_lag_seconds      as integer)    as refresh_lag_seconds
from {{ source('omnichannel_oms', 'inventory_position') }}
