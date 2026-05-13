-- Vault link: product x promo x store (the promo_line grain).
{{ config(materialized='ephemeral') }}

with src as (
    select promo_line_id, promo_id, product_id, store_id
    from {{ ref('stg_pricing_and_promotions__promo_line') }}
    where promo_line_id is not null
)

select
    md5(promo_line_id)                                  as l_promoline_hk,
    md5(product_id)                                     as h_product_hk,
    md5(store_id)                                       as h_store_hk,
    md5(promo_id)                                       as h_promo_hk,
    promo_line_id                                       as promo_line_bk,
    current_date                                        as load_date,
    'pricing_and_promotions.promo_line'                 as record_source
from src
