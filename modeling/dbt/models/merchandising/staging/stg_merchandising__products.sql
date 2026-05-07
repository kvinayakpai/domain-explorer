-- Staging: SKU master.
{{ config(materialized='view') }}

select
    cast(sku           as varchar) as sku,
    cast(product_name  as varchar) as product_name,
    cast(vendor_id     as varchar) as vendor_id,
    cast(category      as varchar) as category,
    cast(subcategory   as varchar) as subcategory,
    cast(msrp          as double)  as msrp,
    cast(cost          as double)  as cost,
    cast(launch_date   as date)    as launch_date,
    cast(active        as boolean) as is_active,
    case
        when cast(msrp as double) > 0
            then (cast(msrp as double) - cast(cost as double)) / cast(msrp as double)
    end                            as margin_at_msrp
from {{ source('merchandising', 'products') }}
