-- Vault hub for the Product (SKU) business key.
{{ config(materialized='ephemeral') }}

with src as (
    select sku_id, gtin
    from {{ ref('stg_trade_promotion_management__product') }}
    where sku_id is not null
)

select
    md5(sku_id)                            as h_product_hk,
    sku_id                                 as product_bk,
    max(gtin)                              as gtin,
    current_date                           as load_date,
    'trade_promotion_management.product'   as record_source
from src
group by sku_id
