-- Product dimension for pharmacovigilance.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_pharmacovigilance__hub_product') }}),
     stg as (select * from {{ ref('stg_pharmacovigilance__products') }})

select
    h.h_product_hk    as product_key,
    h.product_bk      as product_id,
    s.tradename,
    s.inn,
    s.atc_code,
    s.form,
    s.ma_country,
    s.approval_year,
    h.load_date       as dim_loaded_at
from hub h
left join stg s on s.product_id = h.product_bk
