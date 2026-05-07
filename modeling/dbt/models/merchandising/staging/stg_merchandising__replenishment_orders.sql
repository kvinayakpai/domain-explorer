-- Staging: replenishment POs.
{{ config(materialized='view') }}

select
    cast(po_id         as varchar)   as po_id,
    cast(sku           as varchar)   as sku,
    cast(store_id      as varchar)   as store_id,
    cast(quantity      as integer)   as quantity,
    cast(ordered_at    as timestamp) as ordered_at,
    cast(expected_at   as timestamp) as expected_at,
    cast(status        as varchar)   as status,
    case
        when cast(expected_at as timestamp) is not null
         and cast(ordered_at  as timestamp) is not null
            then date_diff('day', cast(ordered_at as timestamp), cast(expected_at as timestamp))
    end                              as expected_lead_time_days
from {{ source('merchandising', 'replenishment_orders') }}
