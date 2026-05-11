-- Staging: individual bid in a bid response.
{{ config(materialized='view') }}

select
    cast(bid_id          as varchar) as bid_id,
    cast(response_id     as varchar) as response_id,
    cast(request_id      as varchar) as request_id,
    cast(imp_id          as varchar) as imp_id,
    cast(advertiser_id   as varchar) as advertiser_id,
    cast(creative_id     as varchar) as creative_id,
    cast(bid_price_cpm   as double)  as bid_price_cpm,
    upper(currency)                  as currency,
    cast(dealid          as varchar) as deal_id,
    cast(iab_categories  as varchar) as iab_categories,
    cast(status          as varchar) as status
from {{ source('programmatic_advertising', 'bid') }}
