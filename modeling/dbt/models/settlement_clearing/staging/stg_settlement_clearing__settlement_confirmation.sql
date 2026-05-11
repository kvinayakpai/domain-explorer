-- Staging: settlement confirmation events (ISO 20022 sese.025).
{{ config(materialized='view') }}

select
    cast(confirmation_id    as varchar)   as confirmation_id,
    cast(ssi_id             as varchar)   as ssi_id,
    cast(trade_id           as varchar)   as trade_id,
    cast(settlement_ts      as timestamp) as settlement_ts,
    cast(settled_quantity   as double)    as settled_quantity,
    cast(settled_amount     as double)    as settled_amount,
    upper(settled_currency)               as settled_currency,
    cast(delivery_indicator as varchar)   as delivery_indicator,
    cast(csd_id             as varchar)   as csd_id
from {{ source('settlement_clearing', 'settlement_confirmation') }}
