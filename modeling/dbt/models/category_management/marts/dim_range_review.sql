-- Range Review dimension.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_category_management__hub_range_review') }}),
     sat as (select * from {{ ref('int_category_management__sat_range_review_state') }})

select
    h.h_range_review_hk    as range_review_sk,
    h.range_review_bk      as range_review_id,
    s.category_id,
    s.banner,
    s.cycle_name,
    s.scheduled_date,
    s.decision_date,
    s.in_market_date,
    s.status,
    s.led_by
from hub h
left join sat s on s.h_range_review_hk = h.h_range_review_hk
