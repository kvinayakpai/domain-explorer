-- Grain: one row per margin call.
{{ config(materialized='table') }}

with mc as (select * from {{ ref('stg_settlement_clearing__margin_call') }}),
     pc as (select * from {{ ref('dim_party_settlement_clearing') }}),
     pd as (select * from {{ ref('dim_party_settlement_clearing') }})

select
    md5(mc.margin_call_id)                                  as margin_call_key,
    mc.margin_call_id,
    mc.calling_party_id,
    pc.party_key                                            as calling_party_key,
    mc.called_party_id,
    pd.party_key                                            as called_party_key,
    mc.call_type,
    mc.call_amount,
    mc.call_currency,
    cast({{ format_date('mc.issued_at', '%Y%m%d') }} as integer)        as issued_date_key,
    mc.issued_at,
    mc.due_at,
    mc.status,
    case when mc.status in ('Settled','Acknowledged') then true else false end as is_resolved
from mc
left join pc on pc.party_id = mc.calling_party_id
left join pd on pd.party_id = mc.called_party_id
