-- Vault link: Invoice ↔ PO ↔ Supplier.
{{ config(materialized='ephemeral') }}

with i as (
    select invoice_id, po_id, supplier_id
    from {{ ref('stg_procurement_spend_analytics__invoice') }}
    where invoice_id is not null
)

select
    md5(invoice_id || '|' || coalesce(po_id, '') || '|' || coalesce(supplier_id, '')) as l_invoice_po_hk,
    md5(invoice_id)                                                                     as h_invoice_hk,
    case when po_id       is not null then md5(po_id)       end                         as h_po_hk,
    case when supplier_id is not null then md5(supplier_id) end                         as h_supplier_hk,
    current_date                                                                         as load_date,
    'procurement_spend_analytics.invoice'                                                as record_source
from i
group by invoice_id, po_id, supplier_id
