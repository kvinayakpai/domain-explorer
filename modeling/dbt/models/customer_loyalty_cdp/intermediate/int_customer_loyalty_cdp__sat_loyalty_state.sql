-- Vault satellite — loyalty account state (tier, balances, status).
{{ config(materialized='ephemeral') }}

select
    md5(loyalty_account_id)                       as h_loyalty_account_hk,
    last_engagement_at                            as load_dts,
    tier_code,
    tier_progress_points,
    current_points_balance,
    lifetime_points_earned,
    lifetime_points_redeemed,
    status,
    opt_in_marketing,
    last_engagement_at,
    'customer_loyalty_cdp.loyalty_account'        as record_source
from {{ ref('stg_customer_loyalty_cdp__loyalty_account') }}
