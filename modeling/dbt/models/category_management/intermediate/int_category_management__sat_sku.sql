-- Vault satellite carrying mutable SKU attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_category_management__skus') }})

select
    md5(sku_id)                                                                       as h_sku_hk,
    current_timestamp                                                                  as load_ts,
    md5(coalesce(brand,'') || '|' || coalesce(category_id,'') || '|' ||
        coalesce(pack_size,'') || '|' || cast(coalesce(list_price_cents,0) as varchar) || '|' ||
        coalesce(lifecycle_stage,'') || '|' || coalesce(status,''))                   as hashdiff,
    brand,
    sub_brand,
    manufacturer,
    category_id,
    pack_size,
    case_pack_qty,
    width_cm,
    height_cm,
    depth_cm,
    list_price_cents,
    srp_cents,
    cost_of_goods_cents,
    private_label_flag,
    lifecycle_stage,
    status,
    'category_management.sku'                                                         as record_source
from src
