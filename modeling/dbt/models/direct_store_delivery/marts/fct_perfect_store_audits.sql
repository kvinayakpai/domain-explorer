-- Fact: one row per Perfect Store audit at a stop. Carries composite score and
--       sub-component lifts (planogram, cooler share, freshness).
{{ config(materialized='table') }}

with a    as (select * from {{ ref('stg_direct_store_delivery__perfect_store_audit') }}),
     s    as (select * from {{ ref('stg_direct_store_delivery__stop') }}),
     dr   as (select * from {{ ref('dim_route') }}),
     do_  as (select * from {{ ref('dim_outlet_dsd') }})

select
    a.audit_id,
    cast(strftime(a.audit_date, '%Y%m%d') as integer)            as date_key,
    do_.outlet_sk,
    dr.route_sk,
    cast(null as varchar)                                         as driver_sk,   -- audits not always driver-keyed
    a.distribution_score,
    a.share_of_cooler_pct,
    a.planogram_compliance_pct,
    a.price_compliance_pct,
    a.promo_compliance_pct,
    a.freshness_score,
    a.perfect_store_score,
    a.oos_count,
    a.is_above_threshold
from a
left join s   on s.stop_id   = a.stop_id
left join dr  on dr.route_id = s.route_id
left join do_ on do_.outlet_id = a.outlet_id
