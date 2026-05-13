-- Staging: payments fact-event source with auth/settlement timestamps.
{{ config(materialized='view') }}

select
    cast(payment_id         as varchar)   as payment_id,
    cast(instruction_id     as varchar)   as instruction_id,
    cast(rail               as varchar)   as rail,
    cast(merchant_id        as varchar)   as merchant_id,
    cast(mcc                as varchar)   as mcc,
    cast(amount             as double)    as amount,
    upper(currency)                       as currency,
    cast(auth_ts            as timestamp) as auth_ts,
    cast(settlement_ts      as timestamp) as settlement_ts,
    cast(auth_status        as varchar)   as auth_status,
    cast(is_stp             as boolean)   as is_stp,
    cast(interchange_amount as double)    as interchange_amount,
    upper(country)                        as country_code,
    case
        when settlement_ts is not null
            then {{ dbt_utils.datediff('auth_ts', 'settlement_ts', 'hour') }}
    end                                   as settlement_latency_hours
from {{ source('payments', 'payments') }}
