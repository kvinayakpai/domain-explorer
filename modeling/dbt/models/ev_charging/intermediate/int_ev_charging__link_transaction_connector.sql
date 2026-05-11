-- Vault-style link between Transaction and Connector.
{{ config(materialized='ephemeral') }}

with src as (
    select transaction_id, connector_id
    from {{ ref('stg_ev_charging__transaction') }}
    where transaction_id is not null and connector_id is not null
)

select
    md5(transaction_id || '|' || connector_id) as l_transaction_connector_hk,
    md5(transaction_id)                        as h_transaction_hk,
    md5(connector_id)                          as h_connector_hk,
    current_date                               as load_date,
    'ev_charging.transaction'                  as record_source
from src
group by transaction_id, connector_id
