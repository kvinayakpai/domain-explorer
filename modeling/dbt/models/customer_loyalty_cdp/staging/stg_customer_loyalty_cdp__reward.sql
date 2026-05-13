{{ config(materialized='view') }}

select
    cast(reward_id              as varchar)    as reward_id,
    cast(reward_name            as varchar)    as reward_name,
    cast(reward_type            as varchar)    as reward_type,
    cast(points_cost            as integer)    as points_cost,
    cast(cash_equivalent_minor  as bigint)     as cash_equivalent_minor,
    cast(stock_remaining        as integer)    as stock_remaining,
    cast(vendor                 as varchar)    as vendor,
    cast(valid_from             as timestamp)  as valid_from,
    cast(valid_to               as timestamp)  as valid_to,
    cast(status                 as varchar)    as status
from {{ source('customer_loyalty_cdp', 'reward') }}
