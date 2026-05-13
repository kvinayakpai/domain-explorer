-- Fact: one row per investigation with duration + recovery + ALTO sharing.
{{ config(materialized='table') }}

with v as (select * from {{ ref('stg_loss_prevention__investigation') }}),
     i as (select * from {{ ref('stg_loss_prevention__incident') }}),
     s as (select * from {{ ref('dim_store_lp') }})

select
    v.investigation_id,
    cast({{ format_date('v.opened_at', '%Y%m%d') }} as integer) as date_key,
    v.incident_id,
    s.store_sk,
    v.investigation_type,
    v.status,
    v.evidence_count,
    v.video_evidence_minutes,
    v.duration_hours,
    v.prosecution_referred,
    v.alto_shared,
    v.opened_at,
    v.closed_at
from v
left join i on i.incident_id = v.incident_id
left join s on s.store_id    = i.store_id
