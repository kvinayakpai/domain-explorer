{{ config(materialized='view') }}

select
    cast(redemption_id          as varchar)    as redemption_id,
    cast(loyalty_account_id     as varchar)    as loyalty_account_id,
    cast(reward_id              as varchar)    as reward_id,
    cast(points_spent           as integer)    as points_spent,
    cast(cash_equivalent_minor  as bigint)     as cash_equivalent_minor,
    cast(channel                as varchar)    as channel,
    cast(order_id               as varchar)    as order_id,
    cast(requested_at           as timestamp)  as requested_at,
    cast(fulfilled_at           as timestamp)  as fulfilled_at,
    cast(status                 as varchar)    as status,
    case
        when fulfilled_at is not null
            then {{ dbt_utils.datediff('requested_at', 'fulfilled_at', 'second') }}
    end                                         as fulfilment_lag_seconds
from {{ source('customer_loyalty_cdp', 'redemption') }}
