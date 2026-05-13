-- Vault link: Tactic -> Promotion -> Product.
{{ config(materialized='ephemeral') }}

with src as (
    select tactic_id, promotion_id, sku_id
    from {{ ref('stg_trade_promotion_management__promo_tactic') }}
)

select
    md5(coalesce(tactic_id,'')||'|'||coalesce(promotion_id,'')||'|'||coalesce(sku_id,'')) as l_link_hk,
    md5(tactic_id)                                              as h_tactic_hk,
    md5(promotion_id)                                           as h_promotion_hk,
    md5(sku_id)                                                 as h_product_hk,
    current_date                                                as load_date,
    'trade_promotion_management.promo_tactic'                   as record_source
from src
where tactic_id is not null
