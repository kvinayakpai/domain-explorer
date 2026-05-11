-- Vault link: Trade ↔ Instrument ↔ owner Party ↔ counterparty.
{{ config(materialized='ephemeral') }}

with t as (
    select trade_id, instrument_id, account_owner_party_id, counterparty_party_id
    from {{ ref('stg_settlement_clearing__trade') }}
    where trade_id is not null
)

select
    md5(trade_id || '|' || coalesce(instrument_id,'') || '|'
        || coalesce(account_owner_party_id,'') || '|' || coalesce(counterparty_party_id,'')) as l_trade_components_hk,
    md5(trade_id)                                                                            as h_trade_hk,
    md5(instrument_id)                                                                       as h_instrument_hk,
    md5(account_owner_party_id)                                                              as h_owner_party_hk,
    md5(counterparty_party_id)                                                               as h_counterparty_hk,
    current_date                                                                             as load_date,
    'settlement_clearing.trade'                                                              as record_source
from t
group by trade_id, instrument_id, account_owner_party_id, counterparty_party_id
