-- Staging: cleared / booked trade.
{{ config(materialized='view') }}

select
    cast(trade_id        as varchar) as trade_id,
    cast(execution_id    as varchar) as execution_id,
    cast(instrument_id   as varchar) as instrument_id,
    cast(account_id      as varchar) as account_id,
    cast(trade_date      as date)    as trade_date,
    cast(settlement_date as date)    as settlement_date,
    cast(side            as varchar) as side,
    cast(quantity        as double)  as quantity,
    cast(price           as double)  as price,
    cast(gross_amount    as double)  as gross_amount,
    upper(currency)                  as currency,
    cast(venue_mic       as varchar) as venue_mic
from {{ source('capital_markets', 'trade') }}
