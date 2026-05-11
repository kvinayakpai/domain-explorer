-- Grain: one row per AMI interval read (meter x ts x OBIS code).
-- FKs: meter_key, service_point_key, read_date_key.
{{ config(materialized='table') }}

with stg as (select * from {{ ref('stg_smart_metering__meter_read') }}),
     l_msp as (select * from {{ ref('int_smart_metering__link_meter_service_point') }})

select
    md5(r.read_id)                                  as read_key,
    r.read_id,
    md5(r.meter_id)                                 as meter_key,
    l_msp.h_service_point_hk                        as service_point_key,
    r.read_date_key,
    r.read_ts,
    r.obis_code,
    r.interval_minutes,
    r.kwh_delivered,
    r.kwh_received,
    r.voltage_v,
    r.current_a,
    r.power_factor,
    r.quality_code,
    case when r.quality_code = 'ESTIMATED' then true else false end as is_estimated,
    case when r.quality_code = 'MISSING'   then true else false end as is_missing
from stg r
left join l_msp on l_msp.h_meter_hk = md5(r.meter_id)
