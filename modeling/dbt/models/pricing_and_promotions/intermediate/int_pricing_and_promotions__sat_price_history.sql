-- Vault satellite — insert-only price history per product x store.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_pricing_and_promotions__price') }})

select
    md5(product_id)                                                                                as h_product_hk,
    md5(store_id)                                                                                  as h_store_hk,
    effective_from                                                                                 as load_ts,
    md5(coalesce(price_type,'') || '|' || cast(coalesce(amount, 0) as varchar) || '|' || coalesce(currency,'')
        || '|' || cast(coalesce(effective_from, cast('1970-01-01' as timestamp)) as varchar)
        || '|' || cast(coalesce(effective_to, cast('1970-01-01' as timestamp)) as varchar)
        || '|' || coalesce(source_system,''))                                                       as hashdiff,
    price_type,
    amount,
    amount_minor,
    currency,
    effective_from,
    effective_to,
    source_system,
    prior_30day_low_minor,
    status,
    'pricing_and_promotions.price'                                                                 as record_source
from src
