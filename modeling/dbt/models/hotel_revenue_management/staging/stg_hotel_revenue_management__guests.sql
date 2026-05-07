-- Staging: guest master.
{{ config(materialized='view') }}

select
    cast(guest_id          as varchar) as guest_id,
    cast(name              as varchar) as guest_name,
    upper(country)                     as country_code,
    cast(loyalty_tier      as varchar) as loyalty_tier,
    cast(lifetime_nights   as integer) as lifetime_nights
from {{ source('hotel_revenue_management', 'guests') }}
