-- Vault satellite carrying mutable Product attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_trade_promotion_management__product') }})

select
    md5(sku_id)                                                                  as h_product_hk,
    current_timestamp                                                            as load_ts,
    md5(coalesce(brand,'') || '|' || coalesce(category,'') || '|' ||
        coalesce(pack_size,'') || '|' || cast(coalesce(list_price_cents,0) as varchar) || '|' ||
        coalesce(status,''))                                                      as hashdiff,
    brand,
    sub_brand,
    category,
    subcategory,
    pack_size,
    case_pack_qty,
    list_price_cents,
    srp_cents,
    cost_of_goods_cents,
    status,
    'trade_promotion_management.product'                                          as record_source
from src
