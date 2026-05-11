-- Vault satellite for Instrument descriptive attributes.
{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_capital_markets__instrument') }})

select
    md5(instrument_id)                                                     as h_instrument_hk,
    current_date                                                           as load_date,
    md5(coalesce(short_name,'') || '|' || coalesce(asset_class,'')
        || '|' || coalesce(currency,'') || '|' || coalesce(status,''))      as hashdiff,
    isin,
    cusip,
    figi,
    cfi_code,
    short_name,
    asset_class,
    currency,
    country_of_issue,
    primary_exchange_mic,
    status,
    'capital_markets.instrument'                                            as record_source
from src
