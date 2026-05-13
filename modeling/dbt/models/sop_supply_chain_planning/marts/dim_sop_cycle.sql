-- S&OP monthly cycle dimension (Oliver Wight 5-step).
{{ config(materialized='table') }}

select
    row_number() over (order by cycle_id)  as cycle_sk,
    cycle_id,
    cycle_start,
    cycle_end,
    product_review_ts,
    demand_review_ts,
    supply_review_ts,
    integrated_reconciliation_ts,
    mbr_ts,
    signed_off_by,
    signed_off_at,
    status
from {{ ref('stg_sop_supply_chain_planning__sop_cycles') }}
