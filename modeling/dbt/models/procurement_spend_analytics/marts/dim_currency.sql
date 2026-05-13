-- Currency dimension. ISO 4217 codes; FX-to-USD recorded as of 2026-05-01.
{{ config(materialized='table') }}

with src as (
    select distinct cast(total_currency as varchar) as currency_code
    from {{ ref('stg_procurement_spend_analytics__purchase_order') }}
    where total_currency is not null
    union
    select distinct cast(total_currency as varchar) as currency_code
    from {{ ref('stg_procurement_spend_analytics__invoice') }}
    where total_currency is not null
)

select
    row_number() over (order by currency_code) as currency_sk,
    currency_code,
    case currency_code
        when 'USD' then 'US Dollar'
        when 'EUR' then 'Euro'
        when 'GBP' then 'Pound Sterling'
        when 'JPY' then 'Japanese Yen'
        when 'CNY' then 'Chinese Yuan'
        when 'INR' then 'Indian Rupee'
        when 'MXN' then 'Mexican Peso'
        when 'BRL' then 'Brazilian Real'
        when 'CAD' then 'Canadian Dollar'
        when 'AUD' then 'Australian Dollar'
        when 'SGD' then 'Singapore Dollar'
        when 'KRW' then 'South Korean Won'
        when 'CHF' then 'Swiss Franc'
        when 'SEK' then 'Swedish Krona'
        else currency_code
    end                                          as currency_name,
    case currency_code
        when 'JPY' then 0
        when 'KRW' then 0
        else 2
    end                                          as minor_unit,
    case currency_code
        when 'USD' then 1.0      when 'EUR' then 1.08
        when 'GBP' then 1.26     when 'JPY' then 0.0067
        when 'CNY' then 0.14     when 'INR' then 0.012
        when 'MXN' then 0.058    when 'BRL' then 0.20
        when 'CAD' then 0.74     when 'AUD' then 0.66
        when 'SGD' then 0.74     when 'KRW' then 0.00076
        when 'CHF' then 1.13     when 'SEK' then 0.095
        else 1.0
    end                                          as fx_rate_to_usd,
    cast('2026-05-01' as date)                   as fx_rate_as_of
from src
