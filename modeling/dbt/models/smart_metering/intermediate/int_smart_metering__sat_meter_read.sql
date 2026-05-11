-- Vault-style satellite carrying interval-read measurements per meter.
{{ config(materialized='ephemeral') }}

with src as (
    select * from {{ ref('stg_smart_metering__meter_read') }}
)

select
    md5(read_id)                                  as h_read_hk,
    md5(meter_id)                                 as h_meter_hk,
    read_ts                                       as load_ts,
    md5(coalesce(obis_code,'') || '|' || coalesce(quality_code,'') || '|'
        || cast(kwh_delivered as varchar))        as hashdiff,
    obis_code,
    interval_minutes,
    kwh_delivered,
    kwh_received,
    voltage_v,
    current_a,
    power_factor,
    quality_code,
    'smart_metering.meter_read'                   as record_source
from src
