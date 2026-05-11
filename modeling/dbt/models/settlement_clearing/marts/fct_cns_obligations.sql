-- Grain: participant x instrument x as_of_date.
{{ config(materialized='table') }}

with c as (select * from {{ ref('stg_settlement_clearing__cns_obligation') }}),
     i as (select * from {{ ref('dim_instrument_settlement_clearing') }}),
     p as (select * from {{ ref('dim_party_settlement_clearing') }})

select
    md5(c.cns_id)                                         as cns_key,
    c.cns_id,
    cast({{ format_date('c.as_of_date', '%Y%m%d') }} as integer)      as as_of_date_key,
    c.as_of_date,
    p.party_key                                            as participant_party_key,
    c.participant_party_id,
    i.instrument_key,
    c.long_position_qty,
    c.short_position_qty,
    c.net_position_qty,
    c.net_position_amount,
    c.currency,
    cast({{ format_date('c.settlement_date', '%Y%m%d') }} as integer) as settlement_date_key
from c
left join i on i.instrument_id = c.instrument_id
left join p on p.party_id      = c.participant_party_id
