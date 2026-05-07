-- Staging: ancillary revenue tied to reservations.
{{ config(materialized='view') }}

select
    cast(ancillary_id   as varchar)   as ancillary_id,
    cast(reservation_id as varchar)   as reservation_id,
    cast(category       as varchar)   as category,
    cast(amount         as double)    as amount,
    cast(ts             as timestamp) as ts
from {{ source('hotel_revenue_management', 'ancillaries') }}
