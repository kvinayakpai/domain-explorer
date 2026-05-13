-- Vault satellite for AP Invoice state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_procurement_spend_analytics__invoice') }})

select
    md5(invoice_id)                                                              as h_invoice_hk,
    coalesce(cast(received_ts as timestamp), cast(invoice_date as timestamp))    as load_ts,
    md5(coalesce(status,'') || '|' || coalesce(match_type,'') || '|'
        || cast(coalesce(total_amount, 0) as varchar) || '|' || cast(coalesce(aging_days, 0) as varchar))
                                                                                 as hashdiff,
    invoice_number,
    invoice_date,
    due_date,
    received_ts,
    total_amount,
    total_currency,
    total_amount_base_usd,
    tax_amount,
    match_type,
    matched,
    paid_ts,
    paid_amount,
    early_pay_discount_taken,
    aging_days,
    peppol_message_id,
    edi_810_doc_no,
    status,
    'procurement_spend_analytics.invoice'                                         as record_source
from src
