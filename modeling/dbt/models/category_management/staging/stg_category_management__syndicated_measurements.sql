{{ config(materialized='view') }}

select
    cast(measurement_id          as varchar)   as measurement_id,
    cast(sku_id                  as varchar)   as sku_id,
    cast(store_id                as varchar)   as store_id,
    cast(category_id             as varchar)   as category_id,
    cast(gtin                    as varchar)   as gtin,
    cast(week_start_date         as date)      as week_start_date,
    cast(geography               as varchar)   as geography,
    cast(units_sold              as bigint)    as units_sold,
    cast(dollars_sold_cents      as bigint)    as dollars_sold_cents,
    cast(avg_retail_price_cents  as bigint)    as avg_retail_price_cents,
    cast(market_share_pct        as double)    as market_share_pct,
    cast(penetration_pct         as double)    as penetration_pct,
    cast(buy_rate_units          as double)    as buy_rate_units,
    cast(any_promo_flag          as boolean)   as any_promo_flag,
    cast(source                  as varchar)   as source,
    cast(panel_id                as varchar)   as panel_id,
    cast(projection_factor       as double)    as projection_factor,
    cast(ingested_at             as timestamp) as ingested_at
from {{ source('category_management', 'syndicated_measurement') }}
