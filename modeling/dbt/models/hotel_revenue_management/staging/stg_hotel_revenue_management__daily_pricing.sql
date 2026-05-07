-- Staging: daily rate / yield decisions per room type / rate plan.
{{ config(materialized='view') }}

select
    cast(pricing_id   as varchar) as pricing_id,
    cast(room_type_id as varchar) as room_type_id,
    cast(rate_plan_id as varchar) as rate_plan_id,
    cast(stay_date    as date)    as stay_date,
    cast(rate         as double)  as rate,
    upper(currency)               as currency,
    cast(yield_score  as double)  as yield_score
from {{ source('hotel_revenue_management', 'daily_pricing') }}
