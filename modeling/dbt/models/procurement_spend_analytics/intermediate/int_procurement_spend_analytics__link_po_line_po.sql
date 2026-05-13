-- Vault link: PO Line ↔ PO ↔ Category.
{{ config(materialized='ephemeral') }}

with l as (
    select po_line_id, po_id, category_code
    from {{ ref('stg_procurement_spend_analytics__po_line') }}
    where po_line_id is not null
)

select
    md5(po_line_id || '|' || coalesce(po_id, '') || '|' || coalesce(category_code, ''))  as l_po_line_po_hk,
    md5(po_line_id)                                                                       as h_po_line_hk,
    case when po_id         is not null then md5(po_id)         end                       as h_po_hk,
    case when category_code is not null then md5(category_code) end                       as h_category_hk,
    current_date                                                                          as load_date,
    'procurement_spend_analytics.po_line'                                                 as record_source
from l
group by po_line_id, po_id, category_code
