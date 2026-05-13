{{ config(materialized='view') }}

select
    cast(scan_id                as varchar)   as scan_id,
    cast(account_id             as varchar)   as account_id,
    cast(outlet_id              as varchar)   as outlet_id,
    cast(sku_id                 as varchar)   as sku_id,
    cast(gtin                   as varchar)   as gtin,
    cast(week_start_date        as date)      as week_start_date,
    cast(units_sold             as bigint)    as units_sold,
    cast(dollars_sold_cents     as bigint)    as dollars_sold_cents,
    cast(avg_retail_price_cents as bigint)    as avg_retail_price_cents,
    cast(on_hand_units          as integer)   as on_hand_units,
    cast(on_promo_flag          as boolean)   as on_promo_flag,
    cast(feature_flag           as boolean)   as feature_flag,
    cast(display_flag           as boolean)   as display_flag,
    cast(tpr_flag               as boolean)   as tpr_flag,
    cast(source_doc             as varchar)   as source_doc,
    cast(ingested_at            as timestamp) as ingested_at
from {{ source('trade_promotion_management', 'retailer_scan_data') }}
