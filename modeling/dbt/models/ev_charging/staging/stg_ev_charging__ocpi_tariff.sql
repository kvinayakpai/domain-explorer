{{ config(materialized='view') }}

select
    cast(tariff_id            as varchar) as tariff_id,
    upper(country_code)                   as country_code,
    cast(party_id             as varchar) as party_id,
    upper(currency)                       as currency,
    cast(tariff_type          as varchar) as tariff_type,
    cast(energy_price_per_kwh as double)  as energy_price_per_kwh,
    cast(time_price_per_hour  as double)  as time_price_per_hour,
    cast(session_fee          as double)  as session_fee,
    cast(min_price            as double)  as min_price,
    cast(max_price            as double)  as max_price,
    cast(valid_from           as date)    as valid_from
from {{ source('ev_charging', 'ocpi_tariff') }}
