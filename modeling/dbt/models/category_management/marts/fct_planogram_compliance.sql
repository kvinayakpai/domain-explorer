-- Fact — store-level planogram-compliance audit observations.
{{ config(materialized='table') }}

with a as (select * from {{ ref('stg_category_management__compliance_audits') }}),
     st as (select * from {{ ref('dim_store_cm') }}),
     pg as (select * from {{ ref('dim_planogram') }})

select
    a.audit_id,
    cast({{ format_date('a.audit_date', '%Y%m%d') }} as integer) as date_key,
    st.store_sk,
    pg.planogram_sk,
    a.audit_date,
    a.positions_audited,
    a.positions_compliant,
    case when a.positions_audited > 0
         then round((a.positions_compliant * 100.0) / a.positions_audited, 2)
         else 0 end                                              as compliance_pct,
    a.missing_facings,
    a.out_of_stock_count,
    a.misplaced_sku_count,
    a.extra_sku_count,
    a.source
from a
left join st on st.store_id     = a.store_id
left join pg on pg.planogram_id = a.planogram_id
