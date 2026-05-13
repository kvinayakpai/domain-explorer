-- Vault link: Contract ↔ Supplier.
{{ config(materialized='ephemeral') }}

with c as (
    select contract_id, supplier_id
    from {{ ref('stg_procurement_spend_analytics__contract') }}
    where contract_id is not null
)

select
    md5(contract_id || '|' || coalesce(supplier_id, ''))    as l_contract_supplier_hk,
    md5(contract_id)                                         as h_contract_hk,
    case when supplier_id is not null then md5(supplier_id) end as h_supplier_hk,
    current_date                                             as load_date,
    'procurement_spend_analytics.contract'                   as record_source
from c
group by contract_id, supplier_id
