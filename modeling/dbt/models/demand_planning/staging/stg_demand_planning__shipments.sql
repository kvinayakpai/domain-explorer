-- Staging: outbound shipments.
{{ config(materialized='view') }}

select
    cast(shipment_id      as varchar)   as shipment_id,
    cast(item_id          as varchar)   as item_id,
    cast(from_location_id as varchar)   as from_location_id,
    cast(customer_id      as varchar)   as customer_id,
    cast(quantity         as double)    as quantity,
    cast(shipped_at       as timestamp) as shipped_at,
    cast(delivered_at     as timestamp) as delivered_at,
    cast(carrier          as varchar)   as carrier,
    cast(on_time          as boolean)   as on_time,
    case
        when cast(delivered_at as timestamp) is not null
         and cast(shipped_at   as timestamp) is not null
            then {{ dbt_utils.datediff('cast(shipped_at as timestamp)', 'cast(delivered_at as timestamp)', 'hour') }}
    end                                 as transit_hours
from {{ source('demand_planning', 'shipments') }}
