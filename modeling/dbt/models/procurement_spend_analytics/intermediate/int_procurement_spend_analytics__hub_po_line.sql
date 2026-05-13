-- Vault hub for the PO Line business key (the spend-cube grain).
{{ config(materialized='ephemeral') }}

select
    md5(po_line_id)                              as h_po_line_hk,
    po_line_id                                   as po_line_bk,
    current_date                                 as load_date,
    'procurement_spend_analytics.po_line'        as record_source
from {{ ref('stg_procurement_spend_analytics__po_line') }}
where po_line_id is not null
group by po_line_id
