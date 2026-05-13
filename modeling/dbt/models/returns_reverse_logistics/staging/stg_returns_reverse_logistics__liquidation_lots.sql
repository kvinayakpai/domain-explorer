{{ config(materialized='view') }}

select
    cast(lot_id              as varchar)    as lot_id,
    cast(marketplace         as varchar)    as marketplace,
    cast(lot_name            as varchar)    as lot_name,
    cast(item_count          as integer)    as item_count,
    cast(total_cogs_minor    as bigint)     as total_cogs_minor,
    cast(starting_bid_minor  as bigint)     as starting_bid_minor,
    cast(winning_bid_minor   as bigint)     as winning_bid_minor,
    cast(proceeds_minor      as bigint)     as proceeds_minor,
    upper(currency)                          as currency,
    cast(listed_ts           as timestamp)  as listed_ts,
    cast(sold_ts             as timestamp)  as sold_ts,
    upper(buyer_country_iso2)                as buyer_country_iso2,
    cast(recovery_pct        as double)     as recovery_pct
from {{ source('returns_reverse_logistics', 'liquidation_lot') }}
