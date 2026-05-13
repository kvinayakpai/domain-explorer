-- Store dimension — _cm suffix avoids collision with merchandising/loss_prevention dim_store.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_category_management__hub_store') }}),
     sat as (select * from {{ ref('int_category_management__sat_store') }})

select
    h.h_store_hk         as store_sk,
    h.store_bk           as store_id,
    s.banner,
    s.store_number,
    s.gln,
    s.country_iso2,
    s.state_region,
    s.postal_code,
    s.format,
    s.cluster_id,
    s.shopper_segment,
    s.total_linear_ft,
    s.status
from hub h
left join sat s on s.h_store_hk = h.h_store_hk
