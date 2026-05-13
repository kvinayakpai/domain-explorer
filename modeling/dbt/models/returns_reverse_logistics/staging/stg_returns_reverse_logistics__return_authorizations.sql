{{ config(materialized='view') }}

select
    cast(rma_id                          as varchar)    as rma_id,
    cast(order_id                        as varchar)    as order_id,
    cast(customer_id                     as varchar)    as customer_id,
    cast(issued_ts                       as timestamp)  as issued_ts,
    cast(expires_ts                      as timestamp)  as expires_ts,
    cast(return_method                   as varchar)    as return_method,
    cast(return_platform                 as varchar)    as return_platform,
    cast(carrier                         as varchar)    as carrier,
    cast(tracking_number                 as varchar)    as tracking_number,
    cast(cross_border                    as boolean)    as cross_border,
    upper(source_country_iso2)                           as source_country_iso2,
    upper(destination_country_iso2)                      as destination_country_iso2,
    cast(rma_status                      as varchar)    as rma_status,
    cast(restocking_fee_eligible_minor   as bigint)     as restocking_fee_eligible_minor,
    cast(epcis_event_uri                 as varchar)    as epcis_event_uri,
    case when rma_status = 'received' then true else false end as is_received,
    case when return_method = 'returnless' then true else false end as is_returnless_method
from {{ source('returns_reverse_logistics', 'return_authorization') }}
