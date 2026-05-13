-- Fact — one row per points-ledger transaction.
-- Joins to dim_customer_cdp via loyalty_account; dim_loyalty_tier by current tier.
{{ config(materialized='table') }}

with l as (select * from {{ ref('stg_customer_loyalty_cdp__points_ledger') }}),
     a as (select * from {{ ref('stg_customer_loyalty_cdp__loyalty_account') }}),
     c as (select * from {{ ref('dim_customer_cdp') }}),
     t as (select * from {{ ref('dim_loyalty_tier') }})

select
    l.ledger_id,
    cast({{ format_date('l.txn_ts', '%Y%m%d') }} as integer) as date_key,
    c.customer_sk,
    t.tier_sk,
    l.loyalty_account_id,
    l.txn_type,
    l.points_delta,
    l.cash_equivalent_minor,
    l.campaign_code,
    case when l.txn_type = 'earn'    then true else false end as is_earn,
    case when l.txn_type = 'redeem'  then true else false end as is_redeem,
    case when l.txn_type = 'expire'  then true else false end as is_expire,
    case when l.txn_type = 'adjust'  then true else false end as is_adjust,
    l.txn_ts,
    l.posted_ts
from l
left join a on a.loyalty_account_id = l.loyalty_account_id
left join c on c.customer_id        = a.customer_id
left join t on t.tier_code          = a.tier_code
