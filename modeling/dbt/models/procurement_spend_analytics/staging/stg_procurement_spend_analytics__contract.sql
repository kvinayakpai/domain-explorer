{{ config(materialized='view') }}

select
    cast(contract_id              as varchar)    as contract_id,
    cast(supplier_id              as varchar)    as supplier_id,
    cast(contract_type            as varchar)    as contract_type,
    cast(parent_contract_id       as varchar)    as parent_contract_id,
    cast(title                    as varchar)    as title,
    cast(effective_date           as date)        as effective_date,
    cast(expiry_date              as date)        as expiry_date,
    cast(auto_renew               as boolean)    as auto_renew,
    cast(notice_period_days       as smallint)   as notice_period_days,
    cast(total_commit_amount      as double)     as total_commit_amount,
    cast(total_commit_currency    as varchar)    as total_commit_currency,
    cast(payment_terms            as varchar)    as payment_terms,
    cast(incoterms                as varchar)    as incoterms,
    cast(rebate_pct               as double)     as rebate_pct,
    cast(rebate_trigger_amount    as double)     as rebate_trigger_amount,
    cast(sustainability_clauses   as varchar)    as sustainability_clauses,
    cast(kpi_clauses              as varchar)    as kpi_clauses,
    cast(contract_value_realized  as double)     as contract_value_realized,
    cast(status                   as varchar)    as status,
    cast(owner_buyer              as varchar)    as owner_buyer,
    cast(meta_extracted_at        as timestamp)  as meta_extracted_at,
    case when sustainability_clauses is not null then true else false end as has_sustainability_clauses,
    case when kpi_clauses is not null then true else false end as has_kpi_clauses
from {{ source('procurement_spend_analytics', 'contract') }}
