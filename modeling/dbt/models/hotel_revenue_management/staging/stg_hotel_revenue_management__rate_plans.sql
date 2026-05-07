-- Staging: rate plans per property.
{{ config(materialized='view') }}

select
    cast(rate_plan_id as varchar) as rate_plan_id,
    cast(property_id  as varchar) as property_id,
    cast(name         as varchar) as rate_plan_name,
    cast(refundable   as boolean) as is_refundable,
    cast(min_los      as integer) as min_los,
    cast(discount_pct as double)  as discount_pct
from {{ source('hotel_revenue_management', 'rate_plans') }}
