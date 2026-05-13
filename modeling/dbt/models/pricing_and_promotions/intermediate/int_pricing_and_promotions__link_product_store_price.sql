-- Vault link bridging product x store x price event.
{{ config(materialized='ephemeral') }}

with src as (
    select price_id, product_id, store_id, effective_from
    from {{ ref('stg_pricing_and_promotions__price') }}
    where price_id is not null
)

select
    md5(price_id)                                    as l_price_hk,
    md5(product_id)                                  as h_product_hk,
    md5(store_id)                                    as h_store_hk,
    price_id                                         as price_bk,
    effective_from,
    current_date                                     as load_date,
    'pricing_and_promotions.price'                   as record_source
from src
