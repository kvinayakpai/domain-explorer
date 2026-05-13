-- Product (SKU) dimension (TPM-suffixed to avoid collision with dim_product in merchandising).
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_trade_promotion_management__hub_product') }}),
     stg as (select * from {{ ref('stg_trade_promotion_management__product') }})

select
    h.h_product_hk         as product_sk,
    h.product_bk           as sku_id,
    h.gtin,
    s.brand,
    s.sub_brand,
    s.category,
    s.subcategory,
    s.pack_size,
    s.case_pack_qty,
    s.list_price_cents,
    s.srp_cents,
    s.cost_of_goods_cents,
    s.launch_date,
    s.status
from hub h
left join stg s on s.sku_id = h.product_bk
