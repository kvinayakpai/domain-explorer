-- Grain: one row per fail event (CSDR penalty / buy-in candidate).
{{ config(materialized='table') }}

with f as (select * from {{ ref('stg_settlement_clearing__failed_settlement') }}),
     si as (select ssi_id, instrument_id, account_owner_party_id, settlement_amount, settlement_currency
            from {{ ref('stg_settlement_clearing__settlement_instruction') }}),
     i  as (select * from {{ ref('dim_instrument_settlement_clearing') }}),
     p  as (select * from {{ ref('dim_party_settlement_clearing') }})

select
    md5(f.failure_id)                                  as fail_key,
    f.failure_id,
    f.ssi_id,
    md5(f.ssi_id)                                      as settlement_key,
    cast({{ format_date('f.failed_at', '%Y%m%d') }} as integer)    as fail_date_key,
    f.failed_at,
    f.estimated_resolution_date,
    f.fail_reason,
    f.csdr_penalty_amount,
    f.status                                            as fail_status,
    si.settlement_amount                                as ssi_amount,
    si.settlement_currency,
    i.instrument_key,
    p.party_key                                         as account_owner_party_key
from f
left join si on si.ssi_id        = f.ssi_id
left join i  on i.instrument_id  = si.instrument_id
left join p  on p.party_id       = si.account_owner_party_id
