-- Staging: merchant master.
{{ config(materialized='view') }}

select
    cast(merchant_id   as varchar) as merchant_id,
    cast(merchant_name as varchar) as merchant_name,
    cast(mcc           as varchar) as mcc,
    cast(description   as varchar) as merchant_description,
    cast(category      as varchar) as merchant_category,
    upper(country)                 as country_code
from {{ source('payments', 'merchants') }}
