-- Staging: CSDR mandatory buy-in events.
{{ config(materialized='view') }}

select
    cast(buyin_id              as varchar)   as buyin_id,
    cast(ssi_id                as varchar)   as ssi_id,
    cast(trigger_reason        as varchar)   as trigger_reason,
    cast(instrument_id         as varchar)   as instrument_id,
    cast(quantity              as double)    as quantity,
    cast(execution_price       as double)    as execution_price,
    cast(executed_at           as timestamp) as executed_at,
    cast(agent_party_id        as varchar)   as agent_party_id,
    cast(settled_at            as timestamp) as settled_at,
    cast(cost_to_failing_party as double)    as cost_to_failing_party
from {{ source('settlement_clearing', 'buyin') }}
