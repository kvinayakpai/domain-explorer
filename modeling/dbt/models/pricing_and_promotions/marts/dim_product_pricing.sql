-- Product dimension scoped to pricing analytics. Type-2 framing
-- (valid_from/valid_to/is_current) preserved for SCD evolution.
-- Suffix `_pricing` avoids collision with merchandising dim_product.
{{ config(materialized='table') }}

select
    row_number() over (order by product_id)        as product_sk,
    product_id,
    gtin,
    sku,
    brand,
    category_id,
    subcategory_id,
    lifecycle_stage,
    kvi_class,
    unit_cost,
    created_at                                     as valid_from,
    cast(null as timestamp)                        as valid_to,
    true                                           as is_current
from {{ ref('stg_pricing_and_promotions__product') }}
