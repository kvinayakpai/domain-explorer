-- Vault hub for the Purchase Order business key.
{{ config(materialized='ephemeral') }}

select
    md5(po_id)                                       as h_po_hk,
    po_id                                            as po_bk,
    current_date                                     as load_date,
    'procurement_spend_analytics.purchase_order'     as record_source
from {{ ref('stg_procurement_spend_analytics__purchase_order') }}
where po_id is not null
group by po_id
