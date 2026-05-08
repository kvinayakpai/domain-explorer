-- Rate plan dimension. One row per rate plan with property + segment context.
{{ config(materialized='table') }}

with rp as (select * from {{ ref('stg_hotel_revenue_management__rate_plans') }}),
     hub_p as (select * from {{ ref('int_hotel_revenue_management__hub_property') }})

select
    md5(rp.rate_plan_id)                                  as rate_plan_key,
    rp.rate_plan_id,
    rp.property_id,
    p.h_property_hk                                       as property_key,
    rp.rate_plan_name,
    rp.is_refundable,
    rp.min_los,
    rp.discount_pct,
    case
        when rp.discount_pct is null              then 'unknown'
        when rp.discount_pct = 0                  then 'rack'
        when rp.discount_pct < 0.10               then 'flexible'
        when rp.discount_pct < 0.20               then 'standard_promo'
        else 'deep_promo'
    end                                                    as plan_segment,
    case
        when rp.min_los is null                   then 'flex'
        when rp.min_los <= 1                      then 'flex'
        when rp.min_los <= 3                      then 'short_los'
        when rp.min_los <= 7                      then 'week_min'
        else 'extended'
    end                                                    as los_segment
from rp
left join hub_p p on p.property_bk = rp.property_id
