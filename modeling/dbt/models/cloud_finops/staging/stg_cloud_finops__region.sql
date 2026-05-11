{{ config(materialized='view') }}

select
    cast(region_id as varchar) as region_id,
    cast(provider  as varchar) as provider,
    cast(geography as varchar) as geography
from {{ source('cloud_finops', 'region') }}
