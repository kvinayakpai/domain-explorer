-- Vault hub for the Invoice business key.
{{ config(materialized='ephemeral') }}

select
    md5(invoice_id)                              as h_invoice_hk,
    invoice_id                                   as invoice_bk,
    current_date                                 as load_date,
    'procurement_spend_analytics.invoice'        as record_source
from {{ ref('stg_procurement_spend_analytics__invoice') }}
where invoice_id is not null
group by invoice_id
