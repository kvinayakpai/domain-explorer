-- Vault link: PO ↔ Supplier ↔ Contract ↔ Category.
{{ config(materialized='ephemeral') }}

with p as (
    select po_id, supplier_id, contract_id, category_code
    from {{ ref('stg_procurement_spend_analytics__purchase_order') }}
    where po_id is not null
)

select
    md5(po_id || '|' || coalesce(supplier_id, '') || '|' || coalesce(contract_id, '')
        || '|' || coalesce(category_code, ''))                                        as l_po_supplier_hk,
    md5(po_id)                                                                         as h_po_hk,
    case when supplier_id   is not null then md5(supplier_id)   end                    as h_supplier_hk,
    case when contract_id   is not null then md5(contract_id)   end                    as h_contract_hk,
    case when category_code is not null then md5(category_code) end                    as h_category_hk,
    current_date                                                                       as load_date,
    'procurement_spend_analytics.purchase_order'                                       as record_source
from p
group by po_id, supplier_id, contract_id, category_code
