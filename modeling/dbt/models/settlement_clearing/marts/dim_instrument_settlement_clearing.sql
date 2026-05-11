-- Instrument dimension for settlement.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_settlement_clearing__hub_instrument') }}),
     stg as (select * from {{ ref('stg_settlement_clearing__instrument') }})

select
    h.h_instrument_hk     as instrument_key,
    h.instrument_bk       as instrument_id,
    s.isin,
    s.cusip,
    s.cfi_code,
    s.short_name,
    s.currency,
    s.country_of_issue,
    s.maturity_date,
    s.status,
    h.load_date           as dim_loaded_at,
    true                  as is_current
from hub h
left join stg s on s.instrument_id = h.instrument_bk
