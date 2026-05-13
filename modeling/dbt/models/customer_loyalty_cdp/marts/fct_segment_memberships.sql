-- Fact — one row per segment membership episode.
{{ config(materialized='table') }}

with m as (select * from {{ ref('stg_customer_loyalty_cdp__segment_membership') }}),
     c as (select * from {{ ref('dim_customer_cdp') }}),
     s as (select * from {{ ref('dim_segment') }})

select
    m.membership_id,
    cast({{ format_date('m.entered_at', '%Y%m%d') }} as integer) as date_key,
    c.customer_sk,
    s.segment_sk,
    m.entered_at,
    m.exited_at,
    m.duration_seconds,
    m.entry_reason,
    m.is_current
from m
left join c on c.customer_id = m.customer_id
left join s on s.segment_id  = m.segment_id
