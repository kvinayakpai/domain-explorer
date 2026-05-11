-- Vault-style satellite carrying descriptive Return attributes.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_tax_administration__return') }}
)

select
    md5(return_id)                                       as h_return_hk,
    filed_at                                             as load_ts,
    md5(coalesce(form_type,'') || '|' || coalesce(filing_status,'') || '|'
        || coalesce(status,'') || '|' || cast(total_tax as varchar))
                                                         as hashdiff,
    tax_year,
    form_type,
    filing_status,
    submission_id,
    is_amended,
    is_extension,
    agi,
    total_income,
    taxable_income,
    total_tax,
    total_payments,
    refund_amount,
    balance_due,
    filing_method,
    status,
    'tax_administration.return'                          as record_source
from src
