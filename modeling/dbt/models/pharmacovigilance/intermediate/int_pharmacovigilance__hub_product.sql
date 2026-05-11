-- Vault-style hub for the Product business key.
{{ config(materialized='ephemeral') }}

with src as (
    select product_id
    from {{ ref('stg_pharmacovigilance__products') }}
    where product_id is not null
)

select
    md5(product_id)                 as h_product_hk,
    product_id                      as product_bk,
    current_date                    as load_date,
    'pharmacovigilance.products'    as record_source
from src
group by product_id
