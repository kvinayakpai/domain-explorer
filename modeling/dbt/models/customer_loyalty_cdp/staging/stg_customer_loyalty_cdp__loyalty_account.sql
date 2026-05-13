{{ config(materialized='view') }}

select
    cast(loyalty_account_id        as varchar)    as loyalty_account_id,
    cast(customer_id               as varchar)    as customer_id,
    cast(program_code              as varchar)    as program_code,
    cast(tier_code                 as varchar)    as tier_code,
    cast(tier_progress_points      as integer)    as tier_progress_points,
    cast(tier_anchor_date          as date)       as tier_anchor_date,
    cast(enrolled_at               as timestamp)  as enrolled_at,
    cast(enrollment_channel        as varchar)    as enrollment_channel,
    cast(lifetime_points_earned    as bigint)     as lifetime_points_earned,
    cast(lifetime_points_redeemed  as bigint)     as lifetime_points_redeemed,
    cast(current_points_balance    as bigint)     as current_points_balance,
    cast(status                    as varchar)    as status,
    cast(opt_in_marketing          as boolean)    as opt_in_marketing,
    cast(last_engagement_at        as timestamp)  as last_engagement_at
from {{ source('customer_loyalty_cdp', 'loyalty_account') }}
