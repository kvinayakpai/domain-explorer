-- Vault satellite for Supplier Risk Assessment payload.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_procurement_spend_analytics__supplier_risk_assessment') }})

select
    md5(assessment_id)                                                          as h_risk_assessment_hk,
    cast(assessment_ts as timestamp)                                            as load_ts,
    md5(coalesce(source,'') || '|' || coalesce(tier,'') || '|'
        || cast(coalesce(overall_score, 0) as varchar))                          as hashdiff,
    assessment_ts,
    source,
    overall_score,
    financial_score,
    operational_score,
    geographic_score,
    cyber_score,
    compliance_score,
    sustainability_score,
    tier,
    mitigation_action,
    valid_until,
    'procurement_spend_analytics.supplier_risk_assessment'                       as record_source
from src
