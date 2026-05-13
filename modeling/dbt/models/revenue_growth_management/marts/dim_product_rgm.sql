{{ config(materialized='table') }}

select
    row_number() over (order by sku_id) as product_sk,
    sku_id,
    gtin,
    brand,
    sub_brand,
    category,
    subcategory,
    lifecycle_stage,
    innovation_flag,
    status
from {{ ref('stg_revenue_growth_management__products') }}
