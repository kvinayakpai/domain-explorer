-- Vault link: Order ↔ Instrument ↔ Account.
{{ config(materialized='ephemeral') }}

with o as (
    select order_id, instrument_id, account_id
    from {{ ref('stg_capital_markets__order') }}
    where order_id is not null
)

select
    md5(order_id || '|' || coalesce(instrument_id,'') || '|' || coalesce(account_id,'')) as l_order_instrument_hk,
    md5(order_id)        as h_order_hk,
    md5(instrument_id)   as h_instrument_hk,
    md5(account_id)      as h_account_hk,
    current_date         as load_date,
    'capital_markets.order' as record_source
from o
group by order_id, instrument_id, account_id
