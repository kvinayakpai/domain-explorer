{{ config(materialized='table') }}

select
    row_number() over (order by disposition_id)  as disposition_sk,
    disposition_id,
    disposition_code,
    disposition_name,
    target_channel,
    typical_recovery_pct,
    lane_owner
from {{ ref('stg_returns_reverse_logistics__dispositions') }}
