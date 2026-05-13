-- Vault hub for the Contract business key.
{{ config(materialized='ephemeral') }}

select
    md5(contract_id)                            as h_contract_hk,
    contract_id                                 as contract_bk,
    current_date                                as load_date,
    'procurement_spend_analytics.contract'      as record_source
from {{ ref('stg_procurement_spend_analytics__contract') }}
where contract_id is not null
group by contract_id
