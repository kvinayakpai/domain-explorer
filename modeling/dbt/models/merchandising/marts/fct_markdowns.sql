-- Grain: one row per markdown event. Surfaces SKU + vendor + product context
-- and computes estimated margin erosion against MSRP.
{{ config(materialized='table') }}

with m  as (select * from {{ ref('stg_merchandising__markdowns') }}),
     pr as (select * from {{ ref('stg_merchandising__products') }}),
     hub_p as (select * from {{ ref('int_merchandising__hub_product') }}),
     hub_v as (select * from {{ ref('int_merchandising__hub_vendor') }})

select
    md5(m.markdown_id)                                  as markdown_key,
    m.markdown_id,
    m.sku,
    p.h_product_hk                                       as product_key,
    pr.vendor_id,
    v.h_vendor_hk                                        as vendor_key,
    pr.category,
    pr.subcategory,
    m.applied_at,
    cast({{ format_date('m.applied_at', '%Y%m%d') }} as integer)    as applied_date_key,
    cast(m.applied_at as date)                           as applied_date,
    m.depth_pct,
    m.reason,
    case
        when m.depth_pct < 0.10 then 'shallow'
        when m.depth_pct < 0.25 then 'standard'
        when m.depth_pct < 0.50 then 'deep'
        else 'clearance'
    end                                                  as markdown_band,
    pr.msrp,
    pr.cost,
    coalesce(pr.msrp, 0.0) * coalesce(m.depth_pct, 0.0)  as price_reduction,
    case
        when pr.msrp > 0
            then pr.msrp * (1 - m.depth_pct)
    end                                                  as effective_unit_price,
    case
        when pr.msrp > 0
            then (pr.msrp * (1 - m.depth_pct)) - pr.cost
    end                                                  as effective_unit_margin
from m
left join pr      on pr.sku       = m.sku
left join hub_p p on p.product_bk = m.sku
left join hub_v v on v.vendor_bk  = pr.vendor_id
