{{ config(materialized='view') }}

select
    cast(product_id                  as varchar)    as product_id,
    cast(gtin                        as varchar)    as gtin,
    cast(sku                         as varchar)    as sku,
    cast(name                        as varchar)    as name,
    cast(category_id                 as varchar)    as category_id,
    cast(hazmat_flag                 as boolean)    as hazmat_flag,
    cast(weight_grams                as integer)    as weight_grams,
    cast(dimensional_weight_grams    as integer)    as dimensional_weight_grams,
    cast(pack_type                   as varchar)    as pack_type,
    cast(status                      as varchar)    as status
from {{ source('omnichannel_oms', 'product') }}
