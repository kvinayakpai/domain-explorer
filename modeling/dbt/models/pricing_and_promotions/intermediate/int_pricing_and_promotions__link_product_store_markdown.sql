-- Vault link: product x store x markdown event.
{{ config(materialized='ephemeral') }}

with src as (
    select markdown_id, product_id, store_id
    from {{ ref('stg_pricing_and_promotions__markdown') }}
    where markdown_id is not null
)

select
    md5(markdown_id)                                as l_markdown_hk,
    md5(product_id)                                 as h_product_hk,
    md5(store_id)                                   as h_store_hk,
    markdown_id                                     as markdown_bk,
    current_date                                    as load_date,
    'pricing_and_promotions.markdown'               as record_source
from src
