{{ config(materialized='view') }}

select
    cast(sku_id              as varchar)  as sku_id,
    cast(gtin                as varchar)  as gtin,
    cast(brand               as varchar)  as brand,
    cast(sub_brand           as varchar)  as sub_brand,
    cast(manufacturer        as varchar)  as manufacturer,
    cast(category_id         as varchar)  as category_id,
    cast(pack_size           as varchar)  as pack_size,
    cast(case_pack_qty       as smallint) as case_pack_qty,
    cast(width_cm            as double)   as width_cm,
    cast(height_cm           as double)   as height_cm,
    cast(depth_cm            as double)   as depth_cm,
    cast(weight_g            as integer)  as weight_g,
    cast(list_price_cents    as bigint)   as list_price_cents,
    cast(srp_cents           as bigint)   as srp_cents,
    cast(cost_of_goods_cents as bigint)   as cost_of_goods_cents,
    cast(private_label_flag  as boolean)  as private_label_flag,
    cast(launch_date         as date)     as launch_date,
    cast(lifecycle_stage     as varchar)  as lifecycle_stage,
    cast(status              as varchar)  as status
from {{ source('category_management', 'sku') }}
