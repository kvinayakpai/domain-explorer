{{ config(materialized='view') }}

select
    cast(cpo_id        as varchar) as cpo_id,
    cast(name          as varchar) as cpo_name,
    upper(country_code)            as country_code,
    cast(ocpi_endpoint as varchar) as ocpi_endpoint
from {{ source('ev_charging', 'cpo') }}
