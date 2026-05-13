-- Vault hub for the Supplier Risk Assessment business key.
{{ config(materialized='ephemeral') }}

select
    md5(assessment_id)                                            as h_risk_assessment_hk,
    assessment_id                                                 as risk_assessment_bk,
    current_date                                                  as load_date,
    'procurement_spend_analytics.supplier_risk_assessment'        as record_source
from {{ ref('stg_procurement_spend_analytics__supplier_risk_assessment') }}
where assessment_id is not null
group by assessment_id
