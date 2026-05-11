-- Staging: light typing on tax_administration.return.
-- NB `return` is a reserved word — we wrap via source() and never reference the
-- raw table name directly downstream.
{{ config(materialized='view') }}

select
    cast(return_id      as varchar)   as return_id,
    cast(taxpayer_id    as varchar)   as taxpayer_id,
    cast(tax_year       as integer)   as tax_year,
    cast(form_type      as varchar)   as form_type,
    cast(filing_status  as varchar)   as filing_status,
    cast(submission_id  as varchar)   as submission_id,
    cast(filed_at       as timestamp) as filed_at,
    cast(due_date       as date)      as due_date,
    cast(is_amended     as boolean)   as is_amended,
    cast(is_extension   as boolean)   as is_extension,
    cast(agi            as double)    as agi,
    cast(total_income   as double)    as total_income,
    cast(taxable_income as double)    as taxable_income,
    cast(total_tax      as double)    as total_tax,
    cast(total_payments as double)    as total_payments,
    cast(refund_amount  as double)    as refund_amount,
    cast(balance_due    as double)    as balance_due,
    cast(filing_method  as varchar)   as filing_method,
    cast(status         as varchar)   as status,
    cast({{ format_date('filed_at', '%Y%m%d') }} as integer) as filed_date_key,
    case
        when filed_at is not null and due_date is not null
            then {{ dbt_utils.datediff('cast(due_date as date)', 'cast(filed_at as date)', 'day') }}
    end as days_late
from {{ source('tax_administration', 'return') }}
