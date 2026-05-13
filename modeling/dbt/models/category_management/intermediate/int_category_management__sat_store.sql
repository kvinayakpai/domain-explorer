-- Vault satellite carrying mutable Store attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_category_management__stores') }})

select
    md5(store_id)                                                                       as h_store_hk,
    current_timestamp                                                                    as load_ts,
    md5(coalesce(banner,'') || '|' || coalesce(format,'') || '|' ||
        coalesce(cluster_id,'') || '|' || coalesce(shopper_segment,'') || '|' ||
        coalesce(status,''))                                                              as hashdiff,
    banner,
    store_number,
    gln,
    country_iso2,
    state_region,
    postal_code,
    format,
    cluster_id,
    shopper_segment,
    total_linear_ft,
    status,
    'category_management.store'                                                          as record_source
from src
