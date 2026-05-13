-- Vault hub for the SKU business key.
{{ config(materialized='ephemeral') }}

with src as (
    select sku_id, gtin
    from {{ ref('stg_category_management__skus') }}
    where sku_id is not null
)

select
    md5(sku_id)                          as h_sku_hk,
    sku_id                               as sku_bk,
    max(gtin)                            as gtin,
    current_date                         as load_date,
    'category_management.sku'            as record_source
from src
group by sku_id
