-- Venue dimension distilled from MIC codes seen in execution + market-data sources.
{{ config(materialized='table') }}

with mics as (
    select distinct venue_mic from {{ ref('stg_capital_markets__execution') }} where venue_mic is not null
    union
    select distinct venue_mic from {{ ref('stg_capital_markets__trade') }}     where venue_mic is not null
    union
    select distinct venue_mic from {{ ref('stg_capital_markets__market_data_snapshot') }} where venue_mic is not null
)

select
    md5(venue_mic)         as venue_key,
    venue_mic              as mic,
    case venue_mic
        when 'XNYS' then 'New York Stock Exchange'
        when 'XNAS' then 'NASDAQ'
        when 'XLON' then 'London Stock Exchange'
        when 'XHKG' then 'Hong Kong Exchanges'
        when 'XTKS' then 'Tokyo Stock Exchange'
        when 'XPAR' then 'Euronext Paris'
        when 'XFRA' then 'Frankfurt Stock Exchange'
        when 'XSWX' then 'SIX Swiss Exchange'
        when 'XASX' then 'ASX (Sydney)'
        when 'XTSE' then 'Toronto Stock Exchange'
        else 'Unknown'
    end                    as venue_name,
    case venue_mic
        when 'XNYS' then 'US' when 'XNAS' then 'US'
        when 'XLON' then 'GB' when 'XHKG' then 'HK'
        when 'XTKS' then 'JP' when 'XPAR' then 'FR'
        when 'XFRA' then 'DE' when 'XSWX' then 'CH'
        when 'XASX' then 'AU' when 'XTSE' then 'CA'
        else null
    end                    as country_iso
from mics
