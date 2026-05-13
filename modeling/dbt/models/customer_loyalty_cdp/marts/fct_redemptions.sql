-- Fact — one row per redemption event.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_customer_loyalty_cdp__redemption') }}),
     a as (select * from {{ ref('stg_customer_loyalty_cdp__loyalty_account') }}),
     c as (select * from {{ ref('dim_customer_cdp') }}),
     rw as (select * from {{ ref('dim_reward') }}),
     ch as (select * from {{ ref('dim_channel') }}),
     t as (select * from {{ ref('dim_loyalty_tier') }})

select
    r.redemption_id,
    cast({{ format_date('r.requested_at', '%Y%m%d') }} as integer) as date_key,
    c.customer_sk,
    rw.reward_sk,
    ch.channel_sk,
    t.tier_sk,
    r.loyalty_account_id,
    r.points_spent,
    r.cash_equivalent_minor,
    case when r.status = 'fulfilled' then true else false end as is_fulfilled,
    case when r.status = 'reversed'  then true else false end as is_reversed,
    r.requested_at,
    r.fulfilled_at,
    r.fulfilment_lag_seconds
from r
left join a  on a.loyalty_account_id = r.loyalty_account_id
left join c  on c.customer_id        = a.customer_id
left join rw on rw.reward_id         = r.reward_id
left join ch on ch.channel_code      = r.channel
left join t  on t.tier_code          = a.tier_code
