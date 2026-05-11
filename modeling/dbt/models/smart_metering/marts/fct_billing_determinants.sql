-- Grain: one row per monthly billing determinant per meter.
{{ config(materialized='table') }}

with bd as (select * from {{ ref('stg_smart_metering__billing_determinant') }})

select
    bd.billing_determinant_id,
    md5(bd.billing_determinant_id)             as bd_key,
    md5(bd.meter_id)                           as meter_key,
    bd.period_start,
    bd.period_end,
    bd.period_start_date_key,
    bd.period_end_date_key,
    bd.kwh_total,
    bd.kwh_peak,
    bd.kwh_offpeak,
    bd.kw_demand,
    bd.rate_schedule,
    bd.is_estimated,
    case when bd.kwh_total > 0
         then round(bd.kwh_peak / bd.kwh_total, 4)
         else null end                          as peak_share
from bd
