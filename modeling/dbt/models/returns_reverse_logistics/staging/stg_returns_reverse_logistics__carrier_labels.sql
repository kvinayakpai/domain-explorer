{{ config(materialized='view') }}

select
    cast(label_id              as varchar)    as label_id,
    cast(rma_id                as varchar)    as rma_id,
    cast(carrier               as varchar)    as carrier,
    cast(service_level         as varchar)    as service_level,
    cast(label_cost_minor      as bigint)     as label_cost_minor,
    cast(prepaid_by_merchant   as boolean)    as prepaid_by_merchant,
    cast(created_ts            as timestamp)  as created_ts,
    cast(scanned_ts            as timestamp)  as scanned_ts,
    cast(delivered_ts          as timestamp)  as delivered_ts,
    cast(status                as varchar)    as status,
    cast(scope3_kg_co2e        as double)     as scope3_kg_co2e
from {{ source('returns_reverse_logistics', 'carrier_label') }}
