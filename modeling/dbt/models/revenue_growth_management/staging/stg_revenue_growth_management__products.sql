{{ config(materialized='view') }}

select
    cast(sku_id          as varchar)   as sku_id,
    cast(gtin            as varchar)   as gtin,
    cast(brand           as varchar)   as brand,
    cast(sub_brand       as varchar)   as sub_brand,
    cast(category        as varchar)   as category,
    cast(subcategory     as varchar)   as subcategory,
    cast(cogs_cents      as bigint)    as cogs_cents,
    cast(launch_date     as date)      as launch_date,
    cast(lifecycle_stage as varchar)   as lifecycle_stage,
    cast(innovation_flag as boolean)   as innovation_flag,
    cast(status          as varchar)   as status
from {{ source('revenue_growth_management', 'product') }}
