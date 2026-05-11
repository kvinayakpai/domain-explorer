-- Grain: one row per OCPP MeterValue sample (~60s cadence).
{{ config(materialized='table') }}

with mv as (select * from {{ ref('stg_ev_charging__meter_value') }}),
     t  as (select * from {{ ref('stg_ev_charging__transaction') }})

select
    md5(mv.meter_value_id)                                 as meter_value_key,
    mv.meter_value_id,
    md5(mv.transaction_id)                                 as transaction_key,
    mv.transaction_id,
    md5(t.connector_id)                                    as connector_key,
    mv.sample_date_key,
    mv.sample_ts,
    mv.ocpp_context,
    mv.energy_register_kwh,
    mv.power_kw,
    mv.current_a,
    mv.voltage_v,
    mv.soc_pct,
    mv.temperature_c
from mv
left join t on t.transaction_id = mv.transaction_id
