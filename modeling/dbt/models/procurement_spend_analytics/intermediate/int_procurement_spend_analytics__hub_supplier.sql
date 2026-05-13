-- Vault hub for the Supplier business key. D&B DUNS recorded alongside.
{{ config(materialized='ephemeral') }}

with src as (
    select supplier_id, duns_number
    from {{ ref('stg_procurement_spend_analytics__supplier') }}
    where supplier_id is not null
)

select
    md5(supplier_id)                          as h_supplier_hk,
    supplier_id                               as supplier_bk,
    max(duns_number)                          as duns_number,
    current_date                              as load_date,
    'procurement_spend_analytics.supplier'    as record_source
from src
group by supplier_id
