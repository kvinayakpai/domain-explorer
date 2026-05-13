-- Vault satellite for PO Line payload — the spend-cube grain attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_procurement_spend_analytics__po_line') }})

select
    md5(po_line_id)                                                              as h_po_line_hk,
    current_timestamp                                                            as load_ts,
    md5(cast(coalesce(line_amount, 0) as varchar) || '|' || coalesce(line_currency,'')
        || '|' || cast(coalesce(scope3_kgco2e, 0) as varchar))                   as hashdiff,
    line_number,
    item_id,
    item_description,
    quantity,
    uom,
    unit_price,
    line_amount,
    line_currency,
    line_amount_base_usd,
    requested_delivery_date,
    tax_amount,
    discount_pct,
    scope3_kgco2e,
    'procurement_spend_analytics.po_line'                                        as record_source
from src
