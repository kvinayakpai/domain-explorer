-- Vault link: Trade ↔ Instrument ↔ Account (and to submitting party via order chain).
{{ config(materialized='ephemeral') }}

with t as (
    select trade_id, instrument_id, account_id, execution_id
    from {{ ref('stg_capital_markets__trade') }}
),
e as (
    select execution_id, order_id from {{ ref('stg_capital_markets__execution') }}
),
o as (
    select order_id, submitting_party_id from {{ ref('stg_capital_markets__order') }}
),
joined as (
    select
        t.trade_id, t.instrument_id, t.account_id, o.submitting_party_id as party_id
    from t
    left join e on e.execution_id = t.execution_id
    left join o on o.order_id     = e.order_id
)

select
    md5(trade_id || '|' || coalesce(instrument_id,'') || '|' || coalesce(account_id,'') || '|' || coalesce(party_id,'')) as l_trade_components_hk,
    md5(trade_id)                              as h_trade_hk,
    md5(instrument_id)                         as h_instrument_hk,
    md5(account_id)                            as h_account_hk,
    case when party_id is null then null else md5(party_id) end as h_party_hk,
    current_date                               as load_date,
    'capital_markets.trade'                    as record_source
from joined
group by trade_id, instrument_id, account_id, party_id
