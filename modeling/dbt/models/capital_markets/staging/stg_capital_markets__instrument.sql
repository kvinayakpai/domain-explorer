-- Staging: instrument master with light typing.
{{ config(materialized='view') }}

select
    cast(instrument_id        as varchar) as instrument_id,
    cast(isin                 as varchar) as isin,
    cast(cusip                as varchar) as cusip,
    cast(figi                 as varchar) as figi,
    cast(cfi_code             as varchar) as cfi_code,
    cast(short_name           as varchar) as short_name,
    cast(asset_class          as varchar) as asset_class,
    upper(currency)                       as currency,
    upper(country_of_issue)               as country_of_issue,
    cast(primary_exchange_mic as varchar) as primary_exchange_mic,
    cast(status               as varchar) as status
from {{ source('capital_markets', 'instrument') }}
