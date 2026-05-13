-- Planogram dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_category_management__hub_planogram') }}),
     sat as (select * from {{ ref('int_category_management__sat_planogram_state') }})

select
    h.h_planogram_hk    as planogram_sk,
    h.planogram_bk      as planogram_id,
    s.category_id,
    s.cluster_id,
    s.version,
    s.effective_from,
    s.effective_to,
    s.total_linear_ft,
    s.total_facings,
    s.total_sku_count,
    s.authoring_system,
    s.status,
    case when s.status in ('approved','in_market') then true else false end as is_current
from hub h
left join sat s on s.h_planogram_hk = h.h_planogram_hk
