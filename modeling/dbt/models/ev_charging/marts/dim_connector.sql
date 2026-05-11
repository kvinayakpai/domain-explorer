-- Connector dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_ev_charging__hub_connector') }}),
     stg as (select * from {{ ref('stg_ev_charging__connector') }})

select
    h.h_connector_hk           as connector_key,
    h.connector_bk             as connector_id,
    s.station_id,
    md5(s.station_id)          as station_key,
    s.evse_id,
    s.connector_position,
    s.connector_type,
    s.power_type,
    s.max_power_kw,
    s.voltage_v,
    s.amperage_a,
    s.status,
    h.load_date                as dim_loaded_at
from hub h
left join stg s on s.connector_id = h.connector_bk
