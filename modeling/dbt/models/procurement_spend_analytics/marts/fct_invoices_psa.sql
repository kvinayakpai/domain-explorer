-- Fact — one row per AP invoice. Suffix `_psa` avoids collision with
-- fct_invoices defined under other anchors (e.g. revenue_cycle, settlement).
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_procurement_spend_analytics__invoice') }}),
     po as (select po_id, contract_id from {{ ref('stg_procurement_spend_analytics__purchase_order') }}),
     s as (select supplier_sk, supplier_id from {{ ref('dim_supplier') }}),
     ct as (select contract_sk, contract_id from {{ ref('dim_contract') }}),
     cur as (select currency_sk, currency_code from {{ ref('dim_currency') }})

select
    i.invoice_id,
    cast({{ format_date('i.invoice_date', '%Y%m%d') }} as integer) as date_key,
    s.supplier_sk,
    ct.contract_sk,
    cur.currency_sk,
    i.invoice_date,
    i.due_date,
    i.paid_ts,
    i.total_amount,
    i.total_amount_base_usd,
    i.tax_amount,
    i.match_type,
    i.matched,
    i.early_pay_discount_taken,
    i.aging_days,
    case
        when i.paid_ts is not null and i.due_date is not null
            then ({{ dbt_utils.datediff('i.due_date', 'i.paid_ts', 'day') }})::smallint
        else 0
    end                                              as paid_late_days,
    i.status
from i
left join po  on po.po_id          = i.po_id
left join s   on s.supplier_id     = i.supplier_id
left join ct  on ct.contract_id    = po.contract_id
left join cur on cur.currency_code = i.total_currency
