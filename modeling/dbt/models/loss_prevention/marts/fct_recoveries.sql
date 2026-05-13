-- Fact: one row per recovery event.
{{ config(materialized='table') }}

with r as (select * from {{ ref('stg_loss_prevention__recovery') }}),
     i as (select * from {{ ref('stg_loss_prevention__incident') }}),
     s as (select * from {{ ref('dim_store_lp') }})

select
    r.recovery_id,
    cast({{ format_date('r.recovered_at', '%Y%m%d') }} as integer) as date_key,
    r.incident_id,
    r.investigation_id,
    s.store_sk,
    r.recovered_amount_minor,
    r.recovery_type,
    r.recovered_at
from r
left join i on i.incident_id = r.incident_id
left join s on s.store_id    = i.store_id
