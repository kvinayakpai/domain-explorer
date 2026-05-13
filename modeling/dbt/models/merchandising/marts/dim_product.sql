-- Product dimension: SKU master joined to vendor for category breakdowns.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_merchandising__hub_product') }}),
     stg as (select * from {{ ref('stg_merchandising__products') }}),
     l   as (select * from {{ ref('int_merchandising__link_product_vendor') }}),
     v   as (select * from {{ ref('stg_merchandising__vendors') }})

select
    h.h_product_hk             as product_key,
    h.product_bk               as sku,
    s.product_name,
    s.category,
    s.subcategory,
    s.vendor_id,
    l.h_vendor_hk              as vendor_key,
    v.vendor_name,
    s.msrp,
    s.cost,
    s.margin_at_msrp,
    s.launch_date,
    s.is_active,
    h.load_date                as dim_loaded_at
from hub h
left join stg s on s.sku             = h.product_bk
left join l    on l.h_product_hk     = h.h_product_hk
left join v    on v.vendor_id        = s.vendor_id
