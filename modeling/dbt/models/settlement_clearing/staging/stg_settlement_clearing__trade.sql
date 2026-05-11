-- Staging: trade headers feeding settlement.
{{ config(materialized='view') }}

select
    cast(trade_id                as varchar) as trade_id,
    cast(instrument_id           as varchar) as instrument_id,
    cast(account_owner_party_id  as varchar) as account_owner_party_id,
    cast(counterparty_party_id   as varchar) as counterparty_party_id,
    cast(side                    as varchar) as side,
    cast(quantity                as double)  as quantity,
    cast(trade_price             as double)  as trade_price,
    cast(trade_date              as date)    as trade_date,
    cast(settlement_date         as date)    as settlement_date,
    cast(clearing_status         as varchar) as clearing_status,
    cast(ccp_id                  as varchar) as ccp_id,
    cast(csd_id                  as varchar) as csd_id
from {{ source('settlement_clearing', 'trade') }}
