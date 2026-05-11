-- Instrument dimension fed from Vault hub + sat.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_capital_markets__hub_instrument') }}),
     sat as (select * from {{ ref('int_capital_markets__sat_instrument_descriptive') }})

select
    h.h_instrument_hk             as instrument_key,
    h.instrument_bk               as instrument_id,
    s.isin,
    s.cusip,
    s.figi,
    s.cfi_code,
    s.short_name,
    s.asset_class,
    s.currency,
    s.country_of_issue,
    s.primary_exchange_mic,
    s.status,
    h.load_date                   as dim_loaded_at,
    true                          as is_current
from hub h
left join sat s on s.h_instrument_hk = h.h_instrument_hk
