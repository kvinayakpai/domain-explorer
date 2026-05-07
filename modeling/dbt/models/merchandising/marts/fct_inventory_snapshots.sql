-- Grain: one row per (snapshot, sku, store).
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_merchandising__inventory_snapshots') }}),
     hub_p as (select * from {{ ref('int_merchandising__hub_product') }}),
     hub_s as (select * from {{ ref('int_merchandising__hub_store') }})

select
    md5(i.snapshot_id)                            as snapshot_key,
    i.snapshot_id,
    i.sku,
    p.h_product_hk                                as product_key,
    i.store_id,
    st.h_store_hk                                 as store_key,
    i.on_hand,
    i.on_order,
    i.safety_stock,
    i.is_below_safety,
    case
        when i.safety_stock > 0
            then (i.on_hand - i.safety_stock)::double / i.safety_stock
    end                                           as cover_above_safety,
    i.as_of,
    cast(strftime(i.as_of, '%Y%m%d') as integer)  as as_of_date_key
from i
left join hub_p p  on p.product_bk = i.sku
left join hub_s st on st.store_bk  = i.store_id
