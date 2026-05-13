{{ config(materialized='view') }}

select
    cast(assessment_id        as varchar)    as assessment_id,
    cast(supplier_id          as varchar)    as supplier_id,
    cast(assessment_ts        as timestamp)  as assessment_ts,
    cast(source               as varchar)    as source,
    cast(overall_score        as double)     as overall_score,
    cast(financial_score      as smallint)   as financial_score,
    cast(operational_score    as smallint)   as operational_score,
    cast(geographic_score     as smallint)   as geographic_score,
    cast(cyber_score          as smallint)   as cyber_score,
    cast(compliance_score     as smallint)   as compliance_score,
    cast(sustainability_score as smallint)   as sustainability_score,
    cast(tier                 as varchar)    as tier,
    cast(mitigation_action    as varchar)    as mitigation_action,
    cast(assessor_user_id     as varchar)    as assessor_user_id,
    cast(valid_until          as date)        as valid_until,
    case when tier in ('high', 'critical') then true else false end as is_high_or_critical
from {{ source('procurement_spend_analytics', 'supplier_risk_assessment') }}
