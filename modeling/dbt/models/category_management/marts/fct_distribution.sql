-- Fact — per store × SKU × week distribution status.
{{ config(materialized='table') }}

with d as (select * from {{ ref('stg_category_management__distribution_records') }}),
     p as (select * from {{ ref('dim_product_cm') }}),
     st as (select * from {{ ref('dim_store_cm') }})

select
    d.distribution_record_id,
    cast({{ format_date('d.week_start_date', '%Y%m%d') }} as integer) as date_key,
    p.product_sk,
    st.store_sk,
    d.week_start_date,
    d.is_listed,
    d.is_on_shelf,
    d.acv_weight,
    d.mandated_flag,
    d.compliant_flag,
    d.source_doc
from d
left join p  on p.sku_id    = d.sku_id
left join st on st.store_id = d.store_id
