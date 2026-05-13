-- Fact — one row per refurb attempt (CRC).
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_returns_reverse_logistics__refurb_outcomes') }}),
     ri as (
         select return_item_id, sku_id
         from {{ ref('stg_returns_reverse_logistics__return_items') }}
     ),
     prod as (select * from {{ ref('dim_product_rrl') }})

select
    r.refurb_outcome_id,
    cast({{ format_date('r.started_ts', '%Y%m%d') }} as integer)             as date_key,
    r.return_item_id,
    prod.product_sk,
    r.crc_id,
    r.started_ts                                                              as started_at,
    r.completed_ts                                                            as completed_at,
    case
        when r.completed_ts is not null and r.started_ts is not null
        then datediff('hour', r.started_ts, r.completed_ts)
        else null
    end                                                                       as cycle_hours,
    r.labor_minutes,
    r.parts_cost_minor,
    r.outcome,
    r.post_refurb_grade,
    r.post_refurb_resale_value_minor,
    r.is_refurbed_resellable                                                  as refurbed_to_resellable
from r
left join ri   on ri.return_item_id = r.return_item_id
left join prod on prod.sku_id       = ri.sku_id
