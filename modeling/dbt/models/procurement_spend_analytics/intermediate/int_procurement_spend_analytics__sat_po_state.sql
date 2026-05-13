-- Vault satellite for PO state.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_procurement_spend_analytics__purchase_order') }})

select
    md5(po_id)                                                                   as h_po_hk,
    cast(po_issued_ts as timestamp)                                              as load_ts,
    md5(coalesce(status,'') || '|' || coalesce(buying_channel,'') || '|'
        || cast(coalesce(total_amount, 0) as varchar) || '|' || coalesce(total_currency,''))
                                                                                 as hashdiff,
    po_number,
    requisition_ts,
    po_issued_ts,
    buying_channel,
    total_amount,
    total_currency,
    total_amount_base_usd,
    payment_terms,
    incoterms,
    status,
    touchless,
    maverick_flag,
    edi_855_received,
    'procurement_spend_analytics.purchase_order'                                  as record_source
from src
