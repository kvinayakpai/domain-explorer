{{ config(materialized='view') }}

select
    cast(invoice_id           as varchar) as invoice_id,
    cast(billing_account_id   as varchar) as billing_account_id,
    cast(invoice_number       as varchar) as invoice_number,
    cast(billing_period_start as date)    as billing_period_start,
    cast(billing_period_end   as date)    as billing_period_end,
    cast(issue_date           as date)    as issue_date,
    cast(due_date             as date)    as due_date,
    cast(subtotal             as double)  as subtotal,
    cast(tax_amount           as double)  as tax_amount,
    cast(total_amount         as double)  as total_amount,
    upper(currency)                       as currency,
    cast(payment_status       as varchar) as payment_status,
    cast({{ format_date('issue_date', '%Y%m%d') }} as integer) as issue_date_key
from {{ source('cloud_finops', 'invoice') }}
