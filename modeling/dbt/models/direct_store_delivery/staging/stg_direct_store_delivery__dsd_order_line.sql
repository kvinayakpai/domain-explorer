{{ config(materialized='view') }}

select
    cast(order_line_id          as varchar) as order_line_id,
    cast(order_id               as varchar) as order_id,
    cast(sku_id                 as varchar) as sku_id,
    cast(gtin                   as varchar) as gtin,
    cast(ordered_units          as integer) as ordered_units,
    cast(ordered_cases          as integer) as ordered_cases,
    cast(delivered_units        as integer) as delivered_units,
    cast(delivered_cases        as integer) as delivered_cases,
    cast(returned_units         as integer) as returned_units,
    cast(short_units            as integer) as short_units,
    cast(unit_price_cents       as bigint)  as unit_price_cents,
    cast(extended_amount_cents  as bigint)  as extended_amount_cents,
    cast(promo_tactic_id        as varchar) as promo_tactic_id,
    cast(lot_number             as varchar) as lot_number,
    cast(expiry_date            as date)    as expiry_date,
    cast(route_load_position    as varchar) as route_load_position,
    -- Derived
    case when ordered_units > 0
         then cast(delivered_units as double) / ordered_units
         else null end as case_fill_rate
from {{ source('direct_store_delivery', 'dsd_order_line') }}
