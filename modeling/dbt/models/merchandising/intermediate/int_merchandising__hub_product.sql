-- Vault-style hub for Product (SKU).
{{ config(materialized='ephemeral') }}

with src as (
    select sku from {{ ref('stg_merchandising__products') }}
    where sku is not null
    union
    select distinct sku from {{ ref('stg_merchandising__sales_lines') }}
    where sku is not null
)

select
    md5(sku)                  as h_product_hk,
    sku                       as product_bk,
    current_date              as load_date,
    'merchandising.products'  as record_source
from src
group by sku
