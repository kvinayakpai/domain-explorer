{{ config(materialized='view') }}

select
    cast(event_id          as varchar)    as event_id,
    cast(customer_id       as varchar)    as customer_id,
    cast(anonymous_id      as varchar)    as anonymous_id,
    cast(event_type        as varchar)    as event_type,
    cast(channel           as varchar)    as channel,
    cast(source_system     as varchar)    as source_system,
    cast(campaign_id       as varchar)    as campaign_id,
    cast(journey_id        as varchar)    as journey_id,
    cast(product_id        as varchar)    as product_id,
    cast(order_id          as varchar)    as order_id,
    cast(amount_minor      as bigint)     as amount_minor,
    upper(currency)                        as currency,
    cast(event_ts          as timestamp)  as event_ts,
    cast(ingest_ts         as timestamp)  as ingest_ts,
    cast(properties_json   as varchar)    as properties_json,
    case
        when ingest_ts is not null and event_ts is not null
            then {{ dbt_utils.datediff('event_ts', 'ingest_ts', 'second') }}
    end                                    as ingest_lag_seconds
from {{ source('customer_loyalty_cdp', 'event') }}
