-- Fact — one row per sold liquidation lot.
{{ config(materialized='table') }}

with l as (select * from {{ ref('stg_returns_reverse_logistics__liquidation_lots') }})

select
    l.lot_id,
    cast({{ format_date('l.sold_ts', '%Y%m%d') }} as integer)                as date_key,
    l.marketplace,
    l.item_count,
    l.total_cogs_minor,
    l.proceeds_minor,
    l.recovery_pct,
    l.currency,
    l.buyer_country_iso2,
    l.listed_ts                                                               as listed_at,
    l.sold_ts                                                                 as sold_at,
    case
        when l.sold_ts is not null and l.listed_ts is not null
        then datediff('day', l.listed_ts, l.sold_ts)
        else null
    end                                                                       as auction_days
from l
