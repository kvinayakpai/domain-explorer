-- Vault hub for the Reward business key.
{{ config(materialized='ephemeral') }}

with src as (
    select reward_id
    from {{ ref('stg_customer_loyalty_cdp__reward') }}
    where reward_id is not null
)

select
    md5(reward_id)                                     as h_reward_hk,
    reward_id                                          as reward_bk,
    current_date                                       as load_date,
    'customer_loyalty_cdp.reward'                      as record_source
from src
group by reward_id
