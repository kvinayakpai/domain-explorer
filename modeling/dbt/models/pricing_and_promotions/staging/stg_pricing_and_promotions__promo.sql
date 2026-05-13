{{ config(materialized='view') }}

select
    cast(promo_id              as varchar)    as promo_id,
    cast(promo_name            as varchar)    as promo_name,
    cast(mechanic              as varchar)    as mechanic,
    cast(discount_pct          as double)     as discount_pct,
    cast(discount_amount_minor as bigint)     as discount_amount_minor,
    cast(start_ts              as timestamp)  as start_ts,
    cast(end_ts                as timestamp)  as end_ts,
    cast(funding_source        as varchar)    as funding_source,
    cast(trade_spend_minor     as bigint)     as trade_spend_minor,
    cast(vendor_id             as varchar)    as vendor_id,
    cast(status                as varchar)    as status,
    cast(created_at            as timestamp)  as created_at
from {{ source('pricing_and_promotions', 'promo') }}
