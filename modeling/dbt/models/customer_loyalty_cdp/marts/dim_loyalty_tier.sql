-- Loyalty tier dimension. Hand-curated ranks + earn multipliers; tier_codes
-- are drawn from the loyalty_account staging view.
{{ config(materialized='table') }}

with tier_universe as (
    select 'bronze'   as tier_code, 1 as tier_rank, 0           as min_spend_minor, 1.00 as earn_multiplier
    union all
    select 'silver',  2, 50000,       1.25
    union all
    select 'gold',    3, 250000,      1.50
    union all
    select 'platinum', 4, 750000,     2.00
    union all
    select 'black',   5, 2000000,     2.50
    union all
    select 'founder', 6, 10000000,    3.00
)

select
    cast(tier_rank as smallint)                 as tier_sk,
    tier_code,
    cast(tier_rank as smallint)                 as tier_rank,
    cast(min_spend_minor as bigint)             as min_spend_minor,
    cast(earn_multiplier as double)             as earn_multiplier
from tier_universe
