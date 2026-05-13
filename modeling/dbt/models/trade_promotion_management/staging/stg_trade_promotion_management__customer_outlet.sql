{{ config(materialized='view') }}

select
    cast(outlet_id     as varchar)   as outlet_id,
    cast(account_id    as varchar)   as account_id,
    cast(store_number  as varchar)   as store_number,
    cast(gln           as varchar)   as gln,
    cast(country_iso2  as varchar)   as country_iso2,
    cast(state_region  as varchar)   as state_region,
    cast(postal_code   as varchar)   as postal_code,
    cast(format        as varchar)   as format,
    cast(lat           as double)    as lat,
    cast(lng           as double)    as lng,
    cast(opened_at     as date)      as opened_at,
    cast(status        as varchar)   as status
from {{ source('trade_promotion_management', 'customer_outlet') }}
