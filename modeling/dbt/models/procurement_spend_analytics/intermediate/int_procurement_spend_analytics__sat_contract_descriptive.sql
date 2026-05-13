-- Vault satellite carrying descriptive Contract attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_procurement_spend_analytics__contract') }})

select
    md5(contract_id)                                                            as h_contract_hk,
    cast(meta_extracted_at as timestamp)                                        as load_ts,
    md5(coalesce(contract_type,'') || '|' || coalesce(status,'') || '|'
        || cast(coalesce(total_commit_amount, 0) as varchar)
        || '|' || coalesce(payment_terms,'') || '|' || coalesce(incoterms,''))  as hashdiff,
    contract_type,
    title,
    effective_date,
    expiry_date,
    auto_renew,
    notice_period_days,
    total_commit_amount,
    total_commit_currency,
    payment_terms,
    incoterms,
    rebate_pct,
    sustainability_clauses,
    kpi_clauses,
    status,
    'procurement_spend_analytics.contract'                                      as record_source
from src
