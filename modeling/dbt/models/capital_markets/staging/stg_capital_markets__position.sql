-- Staging: end-of-day positions.
{{ config(materialized='view') }}

select
    cast(position_id   as varchar) as position_id,
    cast(account_id    as varchar) as account_id,
    cast(instrument_id as varchar) as instrument_id,
    cast(as_of_date    as date)    as as_of_date,
    cast(quantity      as double)  as quantity,
    cast(average_price as double)  as average_price,
    cast(market_value  as double)  as market_value,
    upper(currency)                as currency
from {{ source('capital_markets', 'position') }}
