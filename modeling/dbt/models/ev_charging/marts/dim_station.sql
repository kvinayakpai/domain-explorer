-- Charging station dimension fed from the Vault hub + staging attributes.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_ev_charging__hub_station') }}),
     stg as (select * from {{ ref('stg_ev_charging__charging_station') }}),
     loc as (select * from {{ ref('stg_ev_charging__location') }})

select
    h.h_station_hk          as station_key,
    h.station_bk            as station_id,
    s.location_id,
    md5(s.location_id)      as location_key,
    l.location_name,
    l.city,
    l.country_code,
    s.vendor,
    s.model,
    s.firmware_version,
    s.ocpp_version,
    s.status,
    s.registered_at,
    s.last_heartbeat_ts,
    h.load_ts               as dim_loaded_at
from hub h
left join stg s on s.station_id  = h.station_bk
left join loc l on l.location_id = s.location_id
