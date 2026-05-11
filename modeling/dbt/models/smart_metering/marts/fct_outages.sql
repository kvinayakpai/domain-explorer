-- Grain: one row per outage event with duration and SAIDI contribution.
{{ config(materialized='table') }}

with o as (select * from {{ ref('stg_smart_metering__outage_event') }})

select
    o.outage_id,
    md5(o.outage_id)                              as outage_key,
    md5(o.service_point_id)                       as service_point_key,
    o.feeder_id,
    o.started_date_key,
    cast({{ format_date('o.restored_at', '%Y%m%d') }} as integer) as restored_date_key,
    o.started_at,
    o.restored_at,
    o.duration_minutes,
    o.cause_code,
    o.customers_affected,
    o.saidi_minutes_contribution,
    case when o.duration_minutes >= 5 then true else false end as counts_for_saidi
from o
