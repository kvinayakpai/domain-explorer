-- Vault hub for the Instrument business key.
{{ config(materialized='ephemeral') }}

with src as (
    select instrument_id, isin
    from {{ ref('stg_capital_markets__instrument') }}
    where instrument_id is not null
)

select
    md5(instrument_id)                  as h_instrument_hk,
    instrument_id                       as instrument_bk,
    max(isin)                           as isin,
    current_date                        as load_date,
    'capital_markets.instrument'        as record_source
from src
group by instrument_id
