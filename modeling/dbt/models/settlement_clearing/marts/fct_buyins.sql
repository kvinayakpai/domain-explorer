-- Grain: one row per CSDR buy-in event.
{{ config(materialized='table') }}

with b as (select * from {{ ref('stg_settlement_clearing__buyin') }}),
     i as (select * from {{ ref('dim_instrument_settlement_clearing') }}),
     p as (select * from {{ ref('dim_party_settlement_clearing') }})

select
    md5(b.buyin_id)                                          as buyin_key,
    b.buyin_id,
    b.ssi_id,
    md5(b.ssi_id)                                            as settlement_key,
    b.trigger_reason,
    b.instrument_id,
    i.instrument_key,
    b.quantity,
    b.execution_price,
    cast({{ format_date('b.executed_at', '%Y%m%d') }} as integer)        as executed_date_key,
    b.executed_at,
    b.agent_party_id,
    p.party_key                                              as agent_party_key,
    b.settled_at,
    b.cost_to_failing_party
from b
left join i on i.instrument_id = b.instrument_id
left join p on p.party_id      = b.agent_party_id
