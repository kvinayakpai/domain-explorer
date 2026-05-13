-- Vault satellite — Promo header terms with history.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_pricing_and_promotions__promo') }})

select
    md5(promo_id)                                                                            as h_promo_hk,
    created_at                                                                               as load_ts,
    md5(coalesce(mechanic,'') || '|' || cast(coalesce(discount_pct, 0) as varchar)
        || '|' || cast(coalesce(discount_amount_minor, 0) as varchar)
        || '|' || coalesce(funding_source,'')
        || '|' || cast(coalesce(trade_spend_minor, 0) as varchar)
        || '|' || coalesce(status,''))                                                       as hashdiff,
    promo_name,
    mechanic,
    discount_pct,
    discount_amount_minor,
    start_ts,
    end_ts,
    funding_source,
    trade_spend_minor,
    vendor_id,
    status,
    'pricing_and_promotions.promo'                                                           as record_source
from src
