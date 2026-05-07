-- Staging: effective-dated price master.
{{ config(materialized='view') }}

select
    cast(price_id        as varchar) as price_id,
    cast(sku             as varchar) as sku,
    cast(store_id        as varchar) as store_id,
    cast(list_price      as double)  as list_price,
    upper(currency)                  as currency,
    cast(effective_from  as date)    as effective_from,
    cast(channel         as varchar) as channel
from {{ source('merchandising', 'prices') }}
