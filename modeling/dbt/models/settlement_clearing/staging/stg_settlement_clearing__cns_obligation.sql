-- Staging: DTCC NSCC Continuous Net Settlement obligations.
{{ config(materialized='view') }}

select
    cast(cns_id                  as varchar) as cns_id,
    cast(as_of_date              as date)    as as_of_date,
    cast(participant_party_id    as varchar) as participant_party_id,
    cast(instrument_id           as varchar) as instrument_id,
    cast(long_position_qty       as double)  as long_position_qty,
    cast(short_position_qty      as double)  as short_position_qty,
    cast(net_position_qty        as double)  as net_position_qty,
    cast(net_position_amount     as double)  as net_position_amount,
    upper(currency)                          as currency,
    cast(settlement_date         as date)    as settlement_date
from {{ source('settlement_clearing', 'cns_obligation') }}
