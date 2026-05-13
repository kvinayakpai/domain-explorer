-- Vault hub for the Promo business key.
{{ config(materialized='ephemeral') }}

with src as (
    select promo_id
    from {{ ref('stg_pricing_and_promotions__promo') }}
    where promo_id is not null
)

select
    md5(promo_id)                       as h_promo_hk,
    promo_id                            as promo_bk,
    current_date                        as load_date,
    'pricing_and_promotions.promo'      as record_source
from src
group by promo_id
