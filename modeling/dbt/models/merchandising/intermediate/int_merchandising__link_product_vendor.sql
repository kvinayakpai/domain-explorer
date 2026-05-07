-- Vault-style link between Product and Vendor.
{{ config(materialized='ephemeral') }}

with src as (
    select sku, vendor_id
    from {{ ref('stg_merchandising__products') }}
    where sku is not null and vendor_id is not null
)

select
    md5(sku || '|' || vendor_id)  as l_product_vendor_hk,
    md5(sku)                      as h_product_hk,
    md5(vendor_id)                as h_vendor_hk,
    current_date                  as load_date,
    'merchandising.products'      as record_source
from src
group by sku, vendor_id
