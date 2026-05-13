-- Fact: one row per incident.
{{ config(materialized='table') }}

with i as (select * from {{ ref('stg_loss_prevention__incident') }}),
     s as (select * from {{ ref('dim_store_lp') }}),
     t as (select * from {{ ref('dim_incident_type') }})

select
    i.incident_id,
    cast({{ format_date('i.incident_ts', '%Y%m%d') }} as integer) as date_key,
    s.store_sk,
    t.incident_type_sk,
    i.incident_type,
    i.suspect_id,
    i.detected_via,
    i.gross_loss_minor,
    i.recovered_minor,
    i.net_loss_minor,
    i.nibrs_code,
    i.status,
    i.is_open,
    i.is_closed_recovered,
    i.is_closed_prosecuted,
    i.is_closed_writeoff,
    i.incident_ts
from i
left join s on s.store_id      = i.store_id
left join t on t.incident_type = i.incident_type
