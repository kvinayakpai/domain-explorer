-- Staging: ISO 20022 sese.023 settlement instruction.
{{ config(materialized='view') }}

select
    cast(ssi_id                   as varchar)   as ssi_id,
    cast(trade_id                 as varchar)   as trade_id,
    cast(account_owner_party_id   as varchar)   as account_owner_party_id,
    cast(safekeeping_account_id   as varchar)   as safekeeping_account_id,
    cast(cash_account_id          as varchar)   as cash_account_id,
    cast(instrument_id            as varchar)   as instrument_id,
    cast(settlement_quantity      as double)    as settlement_quantity,
    cast(settlement_amount        as double)    as settlement_amount,
    upper(settlement_currency)                  as settlement_currency,
    cast(trade_date               as date)      as trade_date,
    cast(settlement_date          as date)      as settlement_date,
    cast(delivery_type            as varchar)   as delivery_type,
    cast(payment_type             as varchar)   as payment_type,
    cast(created_at               as timestamp) as created_at,
    cast(status                   as varchar)   as status
from {{ source('settlement_clearing', 'settlement_instruction') }}
