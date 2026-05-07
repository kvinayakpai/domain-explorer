-- Store dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_merchandising__hub_store') }}),
     stg as (select * from {{ ref('stg_merchandising__stores') }})

select
    h.h_store_hk    as store_key,
    h.store_bk      as store_id,
    s.store_name,
    s.country_code,
    s.region,
    s.store_format,
    s.open_date,
    s.is_active,
    h.load_date     as dim_loaded_at
from hub h
left join stg s on s.store_id = h.store_bk
