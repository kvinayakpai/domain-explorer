{{ config(materialized='view') }}

-- One row per refinery.
select
    cast(site_id     as varchar ) as site_id,
    cast(site_name   as varchar ) as site_name,
    cast(operator_id as varchar ) as operator_id,
    cast(time_zone   as varchar ) as time_zone
from {{ source('refinery_operations', 'site') }}
