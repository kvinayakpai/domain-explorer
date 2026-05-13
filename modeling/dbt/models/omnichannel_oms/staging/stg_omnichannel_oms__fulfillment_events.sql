{{ config(materialized='view') }}

select
    cast(event_id          as varchar)    as event_id,
    cast(allocation_id     as varchar)    as allocation_id,
    cast(order_line_id     as varchar)    as order_line_id,
    cast(location_id       as varchar)    as location_id,
    cast(event_type        as varchar)    as event_type,
    cast(occurred_at       as timestamp)  as occurred_at,
    cast(actor_role        as varchar)    as actor_role,
    cast(actor_id          as varchar)    as actor_id,
    cast(payload_json      as varchar)    as payload_json
from {{ source('omnichannel_oms', 'fulfillment_event') }}
