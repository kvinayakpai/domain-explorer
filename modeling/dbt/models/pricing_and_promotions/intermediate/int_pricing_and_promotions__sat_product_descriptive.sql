-- Vault satellite — mutable Product descriptive attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_pricing_and_promotions__product') }})

select
    md5(product_id)                                                                    as h_product_hk,
    created_at                                                                         as load_ts,
    md5(coalesce(name,'') || '|' || coalesce(brand,'') || '|' || coalesce(category_id,'')
        || '|' || coalesce(subcategory_id,'') || '|' || coalesce(lifecycle_stage,'')
        || '|' || coalesce(kvi_class,'') || '|' || cast(coalesce(unit_cost, 0) as varchar))  as hashdiff,
    name,
    brand,
    category_id,
    subcategory_id,
    lifecycle_stage,
    kvi_class,
    unit_cost,
    'pricing_and_promotions.product'                                                   as record_source
from src
