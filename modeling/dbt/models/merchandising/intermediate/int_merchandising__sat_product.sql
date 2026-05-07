-- Vault-style satellite for Product attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_merchandising__products') }}
)

select
    md5(sku)                                                  as h_product_hk,
    coalesce(launch_date, current_date)                       as load_date,
    md5(coalesce(category,'') || '|' || coalesce(subcategory,'') || '|'
        || cast(msrp as varchar) || '|' || cast(cost as varchar))
                                                              as hashdiff,
    product_name,
    category,
    subcategory,
    msrp,
    cost,
    margin_at_msrp,
    is_active,
    'merchandising.products'                                  as record_source
from src
