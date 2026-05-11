-- Staging: collateral pledge / return / substitution.
{{ config(materialized='view') }}

select
    cast(collateral_movement_id     as varchar)   as collateral_movement_id,
    cast(collateral_giver_party_id  as varchar)   as collateral_giver_party_id,
    cast(collateral_taker_party_id  as varchar)   as collateral_taker_party_id,
    cast(direction                  as varchar)   as direction,
    cast(collateral_type            as varchar)   as collateral_type,
    cast(quantity                   as double)    as quantity,
    cast(market_value               as double)    as market_value,
    cast(haircut_pct                as double)    as haircut_pct,
    cast(post_haircut_value         as double)    as post_haircut_value,
    upper(currency)                               as currency,
    cast(movement_ts                as timestamp) as movement_ts,
    cast(status                     as varchar)   as status
from {{ source('settlement_clearing', 'collateral_movement') }}
