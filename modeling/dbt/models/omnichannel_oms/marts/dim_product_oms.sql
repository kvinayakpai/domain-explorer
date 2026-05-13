{{ config(materialized='table') }}

select
    row_number() over (order by product_id) as product_sk,
    product_id,
    sku,
    gtin,
    name,
    category_id,
    hazmat_flag,
    weight_grams,
    pack_type,
    status
from {{ ref('stg_omnichannel_oms__products') }}
