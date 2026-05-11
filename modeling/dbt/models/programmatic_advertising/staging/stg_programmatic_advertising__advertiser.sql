-- Staging: advertiser master.
{{ config(materialized='view') }}

select
    cast(advertiser_id   as varchar) as advertiser_id,
    cast(name            as varchar) as advertiser_name,
    cast(iab_categories  as varchar) as iab_categories,
    upper(country)                   as country_iso,
    cast(tier            as varchar) as tier
from {{ source('programmatic_advertising', 'advertiser') }}
