-- Vault satellite: Creative descriptive attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_programmatic_advertising__creative') }})

select
    md5(creative_id)                                                            as h_creative_hk,
    current_date                                                                as load_date,
    md5(coalesce(ad_format,'') || '|' || coalesce(approval_status,'')
        || '|' || coalesce(vast_version,'')
        || '|' || cast(coalesce(width, 0) as varchar)
        || 'x' || cast(coalesce(height, 0) as varchar))                          as hashdiff,
    ad_format,
    width,
    height,
    duration_sec,
    iab_categories,
    vast_version,
    approval_status,
    'programmatic_advertising.creative'                                          as record_source
from src
