-- Vault hub for Party (settlement view).
{{ config(materialized='ephemeral') }}

with src as (
    select party_id, lei
    from {{ ref('stg_settlement_clearing__party') }}
    where party_id is not null
)

select
    md5(party_id)                       as h_party_hk,
    party_id                            as party_bk,
    max(lei)                            as lei,
    current_date                        as load_date,
    'settlement_clearing.party'         as record_source
from src
group by party_id
