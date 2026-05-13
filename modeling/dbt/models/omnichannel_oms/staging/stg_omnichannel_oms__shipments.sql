{{ config(materialized='view') }}

select
    cast(shipment_id              as varchar)    as shipment_id,
    cast(allocation_id            as varchar)    as allocation_id,
    cast(tracking_number          as varchar)    as tracking_number,
    cast(carrier                  as varchar)    as carrier,
    cast(service_level            as varchar)    as service_level,
    cast(ship_from_location_id    as varchar)    as ship_from_location_id,
    cast(ship_to_postal           as varchar)    as ship_to_postal,
    upper(ship_to_country_iso2)                   as ship_to_country_iso2,
    cast(weight_grams             as integer)    as weight_grams,
    cast(cost_minor               as bigint)     as cost_minor,
    cast(shipped_at               as timestamp)  as shipped_at,
    cast(delivered_at             as timestamp)  as delivered_at,
    cast(status                   as varchar)    as status,
    case when status = 'delivered' then true else false end as is_delivered,
    case
        when shipped_at is not null and delivered_at is not null
            then {{ dbt_utils.datediff('shipped_at', 'delivered_at', 'hour') }}
    end as transit_hours
from {{ source('omnichannel_oms', 'shipment') }}
