{{ config(materialized='view') }}

select
    cast(cycle_id                     as varchar)   as cycle_id,
    cast(cycle_start                  as date)      as cycle_start,
    cast(cycle_end                    as date)      as cycle_end,
    cast(product_review_ts            as timestamp) as product_review_ts,
    cast(demand_review_ts             as timestamp) as demand_review_ts,
    cast(supply_review_ts             as timestamp) as supply_review_ts,
    cast(integrated_reconciliation_ts as timestamp) as integrated_reconciliation_ts,
    cast(mbr_ts                       as timestamp) as mbr_ts,
    cast(signed_off_by                as varchar)   as signed_off_by,
    cast(signed_off_at                as timestamp) as signed_off_at,
    cast(status                       as varchar)   as status
from {{ source('sop_supply_chain_planning', 'sop_cycle') }}
