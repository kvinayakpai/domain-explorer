-- Staging: B2B customer master.
{{ config(materialized='view') }}

select
    cast(customer_id  as varchar) as customer_id,
    cast(name         as varchar) as customer_name,
    cast(channel      as varchar) as channel,
    cast(credit_limit as double)  as credit_limit,
    upper(country)                as country_code,
    cast(tier         as varchar) as tier
from {{ source('demand_planning', 'customers_b2b') }}
