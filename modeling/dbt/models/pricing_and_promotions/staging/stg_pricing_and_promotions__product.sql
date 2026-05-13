{{ config(materialized='view') }}

select
    cast(product_id      as varchar)    as product_id,
    cast(gtin            as varchar)    as gtin,
    cast(sku             as varchar)    as sku,
    cast(name            as varchar)    as name,
    cast(brand           as varchar)    as brand,
    cast(category_id     as varchar)    as category_id,
    cast(subcategory_id  as varchar)    as subcategory_id,
    cast(lifecycle_stage as varchar)    as lifecycle_stage,
    cast(kvi_class       as varchar)    as kvi_class,
    cast(unit_cost       as double)     as unit_cost,
    cast(created_at      as timestamp)  as created_at
from {{ source('pricing_and_promotions', 'product') }}
