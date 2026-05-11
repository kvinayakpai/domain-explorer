-- Vault-style hub for the Connector business key.
{{ config(materialized='ephemeral') }}

with src as (
    select connector_id from {{ ref('stg_ev_charging__connector') }}
    where connector_id is not null
)

select
    md5(connector_id)            as h_connector_hk,
    connector_id                 as connector_bk,
    current_date                 as load_date,
    'ev_charging.connector'      as record_source
from src
group by connector_id
