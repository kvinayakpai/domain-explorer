-- Staging: reservation cancellations.
{{ config(materialized='view') }}

select
    cast(cancellation_id as varchar)   as cancellation_id,
    cast(reservation_id  as varchar)   as reservation_id,
    cast(cancelled_at    as timestamp) as cancelled_at,
    cast(reason          as varchar)   as reason,
    cast(fee_amount      as double)    as fee_amount
from {{ source('hotel_revenue_management', 'cancellations') }}
