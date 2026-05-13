-- Fact — promo performance at the promo_line grain.
-- Includes planned vs actual lift, funding, and a heuristic incremental margin.
{{ config(materialized='table') }}

with l as (select * from {{ ref('stg_pricing_and_promotions__promo_line') }}),
     pr as (select * from {{ ref('dim_promo') }}),
     prd as (select * from {{ ref('dim_product_pricing') }}),
     str as (select * from {{ ref('dim_store_pricing') }})

select
    l.promo_line_id,
    cast({{ format_date('pr.start_ts', '%Y%m%d') }} as integer) as date_key,
    pr.promo_sk,
    prd.product_sk,
    str.store_sk,
    l.planned_baseline_units,
    l.actual_units,
    l.actual_lift_pct,
    l.planned_funding_minor,
    l.actual_funding_minor,
    -- Heuristic: incremental margin = (actual - planned baseline) * unit margin (10% of unit cost as a placeholder).
    cast(coalesce((l.actual_units - l.planned_baseline_units), 0) * 100 * 1.0 as bigint) as incremental_margin_minor,
    case
        when l.actual_funding_minor > 0
        then cast((l.actual_units - l.planned_baseline_units) as double) * 100.0 / l.actual_funding_minor
        else null
    end                                                                                  as promo_roi,
    case when l.cannibalization_flag then cast(l.actual_units * 0.10 as integer)
         else 0 end                                                                       as cannibalization_units,
    case when not l.cannibalization_flag and l.actual_units > l.planned_baseline_units
         then cast(l.actual_units * 0.05 as integer) else 0 end                           as halo_units,
    l.cannibalization_flag                                                                as is_cannibalized
from l
left join pr  on pr.promo_id     = l.promo_id
left join prd on prd.product_id  = l.product_id
left join str on str.store_id    = l.store_id
