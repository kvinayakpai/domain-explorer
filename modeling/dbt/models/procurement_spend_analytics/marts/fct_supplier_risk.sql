-- Fact — one row per supplier_risk_assessment. Surfaces the supplier risk
-- trend; carries a delta-vs-prior score for spike detection.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_procurement_spend_analytics__supplier_risk_assessment') }}),
     s as (select supplier_sk, supplier_id from {{ ref('dim_supplier') }}),
     prior as (
        select
            supplier_id,
            assessment_ts,
            overall_score,
            lag(overall_score) over (partition by supplier_id order by assessment_ts) as prior_score
        from r
     )

select
    r.assessment_id,
    cast({{ format_date('r.assessment_ts', '%Y%m%d') }} as integer) as date_key,
    s.supplier_sk,
    r.assessment_ts,
    r.source,
    r.overall_score,
    r.financial_score,
    r.operational_score,
    r.geographic_score,
    r.cyber_score,
    r.compliance_score,
    r.sustainability_score,
    r.tier,
    r.is_high_or_critical                                                    as is_critical_tier,
    coalesce(r.overall_score - p.prior_score, 0.0)                           as delta_vs_prior
from r
left join s on s.supplier_id = r.supplier_id
left join prior p on p.supplier_id = r.supplier_id and p.assessment_ts = r.assessment_ts
