-- Category hierarchy dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_category_management__hub_category') }}),
     sat as (select * from {{ ref('int_category_management__sat_category') }})

select
    h.h_category_hk           as category_sk,
    h.category_bk             as category_id,
    s.category_name,
    s.parent_category_id,
    s.category_level,
    s.category_role,
    s.linear_ft_target,
    s.gpc_brick,
    s.status
from hub h
left join sat s on s.h_category_hk = h.h_category_hk
