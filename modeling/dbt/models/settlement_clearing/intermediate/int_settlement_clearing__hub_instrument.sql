-- Vault hub for Instrument (settlement view).
{{ config(materialized='ephemeral') }}

with src as (
    select instrument_id, isin
    from {{ ref('stg_settlement_clearing__instrument') }}
    where instrument_id is not null
)

select
    md5(instrument_id)                       as h_instrument_hk,
    instrument_id                            as instrument_bk,
    max(isin)                                as isin,
    current_date                             as load_date,
    'settlement_clearing.instrument'         as record_source
from src
group by instrument_id
