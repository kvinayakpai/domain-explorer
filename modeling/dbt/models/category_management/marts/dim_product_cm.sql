-- Product (SKU) dimension — _cm suffix to avoid collisions with TPM / RGM dim_product.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_category_management__hub_sku') }}),
     sat as (select * from {{ ref('int_category_management__sat_sku') }}),
     stg as (select * from {{ ref('stg_category_management__skus') }})

select
    h.h_sku_hk            as product_sk,
    h.sku_bk              as sku_id,
    h.gtin,
    s.brand,
    s.sub_brand,
    s.manufacturer,
    s.category_id,
    s.pack_size,
    s.case_pack_qty,
    s.width_cm,
    s.height_cm,
    s.depth_cm,
    s.list_price_cents,
    s.srp_cents,
    s.cost_of_goods_cents,
    s.private_label_flag,
    s.lifecycle_stage,
    s.status,
    stg.launch_date,
    true                   as is_current
from hub h
left join sat s on s.h_sku_hk = h.h_sku_hk
left join stg on stg.sku_id  = h.sku_bk
