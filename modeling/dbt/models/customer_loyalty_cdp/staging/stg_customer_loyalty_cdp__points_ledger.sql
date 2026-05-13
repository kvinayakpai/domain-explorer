{{ config(materialized='view') }}

select
    cast(ledger_id              as varchar)    as ledger_id,
    cast(loyalty_account_id     as varchar)    as loyalty_account_id,
    cast(txn_type               as varchar)    as txn_type,
    cast(source_event_id        as varchar)    as source_event_id,
    cast(order_id               as varchar)    as order_id,
    cast(points_delta           as bigint)     as points_delta,
    cast(cash_equivalent_minor  as bigint)     as cash_equivalent_minor,
    cast(campaign_code          as varchar)    as campaign_code,
    cast(txn_ts                 as timestamp)  as txn_ts,
    cast(posted_ts              as timestamp)  as posted_ts,
    cast(expiry_ts              as timestamp)  as expiry_ts,
    cast(status                 as varchar)    as status
from {{ source('customer_loyalty_cdp', 'points_ledger') }}
