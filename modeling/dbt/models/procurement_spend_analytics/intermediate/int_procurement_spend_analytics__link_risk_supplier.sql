-- Vault link: Supplier Risk Assessment ↔ Supplier.
{{ config(materialized='ephemeral') }}

with r as (
    select assessment_id, supplier_id
    from {{ ref('stg_procurement_spend_analytics__supplier_risk_assessment') }}
    where assessment_id is not null
)

select
    md5(assessment_id || '|' || coalesce(supplier_id, ''))           as l_risk_supplier_hk,
    md5(assessment_id)                                                as h_risk_assessment_hk,
    case when supplier_id is not null then md5(supplier_id) end       as h_supplier_hk,
    current_date                                                      as load_date,
    'procurement_spend_analytics.supplier_risk_assessment'            as record_source
from r
group by assessment_id, supplier_id
