-- Vault satellite for Party descriptors.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_settlement_clearing__party') }})

select
    md5(party_id)                                                            as h_party_hk,
    current_date                                                             as load_date,
    md5(coalesce(party_role,'') || '|' || coalesce(country_iso,'')
        || '|' || coalesce(status,''))                                        as hashdiff,
    legal_name,
    party_role,
    country_iso,
    bic,
    lei,
    status,
    'settlement_clearing.party'                                               as record_source
from src
