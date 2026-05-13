-- Vault hub for the Product business key.
{{ config(materialized='ephemeral') }}

with src as (
    select product_id, gtin
    from {{ ref('stg_pricing_and_promotions__product') }}
    where product_id is not null
)

select
    md5(product_id)                       as h_product_hk,
    product_id                            as product_bk,
    max(gtin)                             as gtin,
    current_date                          as load_date,
    'pricing_and_promotions.product'      as record_source
from src
group by product_id
