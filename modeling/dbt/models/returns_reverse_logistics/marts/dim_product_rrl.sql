-- Product dimension scoped to the returns universe. Built from the return_item
-- staging view's distinct SKU set. "_rrl" suffix avoids collision with the
-- merchandising / pricing_and_promotions dim_product.
{{ config(materialized='table') }}

with src as (
    select
        sku_id,
        any_value(gtin)              as gtin,
        any_value(category)          as category,
        avg(unit_cogs_minor)         as unit_cogs_minor,
        avg(unit_retail_minor)       as unit_retail_minor
    from {{ ref('stg_returns_reverse_logistics__return_items') }}
    group by sku_id
)

select
    row_number() over (order by sku_id)   as product_sk,
    sku_id,
    gtin,
    category,
    cast(unit_cogs_minor   as bigint)     as unit_cogs_minor,
    cast(unit_retail_minor as bigint)     as unit_retail_minor
from src
