-- Contract dimension. Surfaces sustainability/KPI clause presence as flags.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_procurement_spend_analytics__contract') }}),
     s as (select * from {{ ref('dim_supplier') }})

select
    row_number() over (order by c.contract_id) as contract_sk,
    c.contract_id,
    s.supplier_sk,
    c.contract_type,
    c.title,
    c.effective_date,
    c.expiry_date,
    c.auto_renew,
    c.payment_terms,
    c.incoterms,
    c.rebate_pct,
    c.total_commit_amount,
    c.total_commit_currency,
    c.has_sustainability_clauses,
    c.has_kpi_clauses,
    c.status
from c
left join s on s.supplier_id = c.supplier_id
