-- Staging: FpML OTC derivative trades.
{{ config(materialized='view') }}

select
    cast(fpml_trade_id     as varchar) as fpml_trade_id,
    cast(product_type      as varchar) as product_type,
    cast(party1_id         as varchar) as party1_id,
    cast(party2_id         as varchar) as party2_id,
    cast(notional          as double)  as notional,
    upper(notional_currency)           as notional_currency,
    cast(trade_date        as date)    as trade_date,
    cast(effective_date    as date)    as effective_date,
    cast(termination_date  as date)    as termination_date,
    cast(fixed_rate        as double)  as fixed_rate,
    cast(floating_index    as varchar) as floating_index,
    cast(day_count_fraction as varchar) as day_count_fraction,
    cast(uti               as varchar) as uti
from {{ source('capital_markets', 'fpml_trade') }}
