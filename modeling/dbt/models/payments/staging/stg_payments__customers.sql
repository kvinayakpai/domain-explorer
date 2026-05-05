-- Staging: light typing + renaming on payments.customers.
{{ config(materialized='view') }}

select
    cast(customer_id  as varchar) as customer_id,
    cast(full_name    as varchar) as full_name,
    cast(email        as varchar) as email,
    upper(country)                as country_code,
    cast(kyc_status   as varchar) as kyc_status,
    cast(risk_segment as varchar) as risk_segment,
    cast(signup_date  as date)    as signup_date
from {{ source('payments', 'customers') }}
