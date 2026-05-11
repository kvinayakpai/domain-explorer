-- Vault hub for the Party / Counterparty business key.
{{ config(materialized='ephemeral') }}

with src as (
    select party_id, lei
    from {{ ref('stg_capital_markets__party') }}
    where party_id is not null
)

select
    md5(party_id)                  as h_party_hk,
    party_id                       as party_bk,
    max(lei)                       as lei,
    current_date                   as load_date,
    'capital_markets.party'        as record_source
from src
group by party_id
