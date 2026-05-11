-- Vault-style hub for the Charging Station business key.
{{ config(materialized='ephemeral') }}

with src as (
    select station_id, registered_at
    from {{ ref('stg_ev_charging__charging_station') }}
    where station_id is not null
)

select
    md5(station_id)                          as h_station_hk,
    station_id                               as station_bk,
    coalesce(min(registered_at), current_date) as load_ts,
    'ev_charging.charging_station'           as record_source
from src
group by station_id
