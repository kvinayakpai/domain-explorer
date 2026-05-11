{{ config(materialized='view') }}

select
    cast(service_name        as varchar) as service_name,
    cast(provider            as varchar) as provider,
    cast(service_category    as varchar) as service_category,
    cast(service_subcategory as varchar) as service_subcategory
from {{ source('cloud_finops', 'service') }}
