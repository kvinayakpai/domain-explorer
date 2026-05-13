-- Reward dimension.
{{ config(materialized='table') }}

select
    row_number() over (order by reward_id)            as reward_sk,
    reward_id,
    reward_name,
    reward_type,
    points_cost,
    cash_equivalent_minor,
    vendor,
    status
from {{ ref('stg_customer_loyalty_cdp__reward') }}
