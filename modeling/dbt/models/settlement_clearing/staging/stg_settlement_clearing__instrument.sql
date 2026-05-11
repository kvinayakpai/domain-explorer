-- Staging: instrument master (settlement view).
{{ config(materialized='view') }}

select
    cast(instrument_id    as varchar) as instrument_id,
    cast(isin             as varchar) as isin,
    cast(cusip            as varchar) as cusip,
    cast(cfi_code         as varchar) as cfi_code,
    cast(short_name       as varchar) as short_name,
    upper(currency)                   as currency,
    upper(country_of_issue)           as country_of_issue,
    cast(maturity_date    as date)    as maturity_date,
    cast(status           as varchar) as status
from {{ source('settlement_clearing', 'instrument') }}
