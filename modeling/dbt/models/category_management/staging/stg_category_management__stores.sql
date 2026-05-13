{{ config(materialized='view') }}

select
    cast(store_id        as varchar)  as store_id,
    cast(banner          as varchar)  as banner,
    cast(store_number    as varchar)  as store_number,
    cast(gln             as varchar)  as gln,
    cast(country_iso2    as varchar)  as country_iso2,
    cast(state_region    as varchar)  as state_region,
    cast(postal_code     as varchar)  as postal_code,
    cast(format          as varchar)  as format,
    cast(cluster_id      as varchar)  as cluster_id,
    cast(shopper_segment as varchar)  as shopper_segment,
    cast(total_linear_ft as double)   as total_linear_ft,
    cast(status          as varchar)  as status
from {{ source('category_management', 'store') }}
