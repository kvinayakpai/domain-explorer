-- Grain: one row per monthly invoice.
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_cloud_finops__invoice') }})

select
    md5(i.invoice_id)                  as invoice_key,
    i.invoice_id,
    md5(i.billing_account_id)          as billing_account_key,
    i.billing_account_id,
    i.invoice_number,
    i.billing_period_start,
    i.billing_period_end,
    i.issue_date,
    i.due_date,
    i.issue_date_key,
    i.subtotal,
    i.tax_amount,
    i.total_amount,
    i.currency,
    i.payment_status,
    case when i.payment_status = 'paid'    then true else false end as is_paid,
    case when i.payment_status = 'overdue' then true else false end as is_overdue
from i
