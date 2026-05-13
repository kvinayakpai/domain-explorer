{{ config(materialized='view') }}

select
    cast(deal_id                   as varchar)  as deal_id,
    cast(promo_plan_id             as varchar)  as promo_plan_id,
    cast(account_id                as varchar)  as account_id,
    cast(pack_id                   as varchar)  as pack_id,
    cast(tactic_type               as varchar)  as tactic_type,
    cast(mechanic                  as varchar)  as mechanic,
    cast(discount_per_unit_cents   as bigint)   as discount_per_unit_cents,
    cast(rebate_pct                as double)   as rebate_pct,
    cast(deal_floor_cents          as bigint)   as deal_floor_cents,
    cast(planned_units             as bigint)   as planned_units,
    cast(planned_spend_cents       as bigint)   as planned_spend_cents,
    cast(actual_units              as bigint)   as actual_units,
    cast(actual_spend_cents        as bigint)   as actual_spend_cents,
    cast(forward_buy_cost_cents    as bigint)   as forward_buy_cost_cents,
    cast(start_date                as date)     as start_date,
    cast(end_date                  as date)     as end_date,
    cast(settlement_method         as varchar)  as settlement_method,
    cast(status                    as varchar)  as status
from {{ source('revenue_growth_management', 'deal') }}
