{{ config(materialized='view') }}

select
    cast(customer_id   as varchar) as customer_id,
    cast(customer_name as varchar) as customer_name,
    cast(channel       as varchar) as channel,
    cast(segment       as varchar) as segment,
    cast(country_iso2  as varchar) as country_iso2,
    cast(region        as varchar) as region,
    cast(priority      as smallint) as priority,
    cast(status        as varchar) as status
from {{ source('sop_supply_chain_planning', 'customer') }}
