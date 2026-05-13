-- Product dimension (DSD-suffixed; merchandising and trade_promotion_management
-- both already publish dim_product / dim_product_tpm).
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_direct_store_delivery__product') }})

select
    md5(sku_id)        as product_sk,
    sku_id,
    gtin,
    brand,
    category,
    subcategory,
    pack_size,
    case_pack_qty,
    list_price_cents,
    srp_cents,
    cost_of_goods_cents,
    refrigerated,
    perishable,
    status
from stg
