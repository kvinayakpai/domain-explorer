{{ config(materialized='view') }}

select
    cast(sku_id              as varchar) as sku_id,
    cast(gtin                as varchar) as gtin,
    cast(brand               as varchar) as brand,
    cast(category            as varchar) as category,
    cast(subcategory         as varchar) as subcategory,
    cast(pack_size           as varchar) as pack_size,
    cast(case_pack_qty       as smallint) as case_pack_qty,
    cast(list_price_cents    as bigint) as list_price_cents,
    cast(srp_cents           as bigint) as srp_cents,
    cast(cost_of_goods_cents as bigint) as cost_of_goods_cents,
    cast(refrigerated        as boolean) as refrigerated,
    cast(perishable          as boolean) as perishable,
    cast(status              as varchar) as status
from {{ source('direct_store_delivery', 'product') }}
