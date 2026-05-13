-- Segment dimension.
{{ config(materialized='table') }}

select
    row_number() over (order by segment_id)         as segment_sk,
    segment_id,
    segment_name,
    segment_kind,
    refresh_cadence,
    owning_team,
    status
from {{ ref('stg_customer_loyalty_cdp__segment') }}
