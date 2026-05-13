-- Vault satellite — mutable Store descriptive attributes (zone, format, banner).
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_pricing_and_promotions__store') }})

select
    md5(store_id)                                                                          as h_store_hk,
    coalesce(cast(open_date as timestamp), current_timestamp)                              as load_ts,
    md5(coalesce(store_name,'') || '|' || coalesce(banner,'') || '|' || coalesce(price_zone_id,'')
        || '|' || coalesce(region,'') || '|' || coalesce(country_iso2,'')
        || '|' || coalesce(format,'') || '|' || coalesce(status,''))                       as hashdiff,
    store_name,
    banner,
    price_zone_id,
    region,
    country_iso2,
    format,
    status,
    'pricing_and_promotions.store'                                                         as record_source
from src
