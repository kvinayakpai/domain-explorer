-- Grain: one row per settlement instruction (terminal sese.023 state).
-- Suffixed name avoids collision with payments/fct_settlements.
{{ config(materialized='table') }}

with si as (select * from {{ ref('stg_settlement_clearing__settlement_instruction') }}),
     t  as (select trade_id, ccp_id, csd_id, counterparty_party_id from {{ ref('stg_settlement_clearing__trade') }}),
     conf as (
        select ssi_id,
               max(settlement_ts) as settled_ts
        from {{ ref('stg_settlement_clearing__settlement_confirmation') }}
        group by ssi_id
     ),
     i as (select * from {{ ref('dim_instrument_settlement_clearing') }}),
     p as (select * from {{ ref('dim_party_settlement_clearing') }}),
     csd as (select * from {{ ref('dim_csd') }})

select
    md5(si.ssi_id)                                          as settlement_key,
    si.ssi_id,
    si.trade_id,
    md5(si.trade_id)                                        as trade_key,
    si.account_owner_party_id,
    p.party_key                                             as account_owner_party_key,
    md5(coalesce(t.counterparty_party_id,''))               as counterparty_key,
    i.instrument_key,
    csd.csd_key,
    cast({{ format_date('si.trade_date', '%Y%m%d') }} as integer)      as trade_date_key,
    cast({{ format_date('si.settlement_date', '%Y%m%d') }} as integer) as settlement_date_key,
    case when conf.settled_ts is not null
         then cast({{ format_date('conf.settled_ts', '%Y%m%d') }} as integer)
         end                                                as settled_date_key,
    si.settlement_quantity,
    si.settlement_amount,
    si.settlement_currency,
    si.delivery_type,
    si.payment_type,
    si.status                                               as final_status,
    case when si.status = 'Settled'  then true else false end as is_settled,
    case when si.status = 'Failed'   then true else false end as is_failed,
    case when conf.settled_ts is not null
         then {{ dbt_utils.datediff('si.trade_date', 'cast(conf.settled_ts as date)', 'day') }}
         end                                                as days_to_settle
from si
left join t    on t.trade_id     = si.trade_id
left join conf on conf.ssi_id    = si.ssi_id
left join i    on i.instrument_id = si.instrument_id
left join p    on p.party_id     = si.account_owner_party_id
left join csd  on csd.csd_id     = t.csd_id
