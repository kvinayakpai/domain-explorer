{{ config(materialized='view') }}

select
    cast(refurb_outcome_id              as varchar)    as refurb_outcome_id,
    cast(return_item_id                 as varchar)    as return_item_id,
    cast(crc_id                         as varchar)    as crc_id,
    cast(started_ts                     as timestamp)  as started_ts,
    cast(completed_ts                   as timestamp)  as completed_ts,
    cast(labor_minutes                  as integer)    as labor_minutes,
    cast(parts_cost_minor               as bigint)     as parts_cost_minor,
    cast(outcome                        as varchar)    as outcome,
    cast(post_refurb_grade              as varchar)    as post_refurb_grade,
    cast(post_refurb_resale_value_minor as bigint)     as post_refurb_resale_value_minor,
    case when outcome in ('refurbed_A','refurbed_B','refurbed_open_box') then true else false end as is_refurbed_resellable
from {{ source('returns_reverse_logistics', 'refurb_outcome') }}
