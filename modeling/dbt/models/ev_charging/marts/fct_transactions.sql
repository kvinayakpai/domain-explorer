-- Grain: one row per OCPP charging transaction.
-- FKs: connector_key, station_key, location_key, started_date_key.
{{ config(materialized='table') }}

with sat as (select * from {{ ref('int_ev_charging__sat_transaction') }}),
     hub as (select * from {{ ref('int_ev_charging__hub_transaction') }}),
     l_tc as (select * from {{ ref('int_ev_charging__link_transaction_connector') }}),
     stg_t as (select * from {{ ref('stg_ev_charging__transaction') }}),
     stg_c as (select * from {{ ref('stg_ev_charging__connector') }})

select
    h.h_transaction_hk                                  as transaction_key,
    h.transaction_bk                                    as transaction_id,
    cast({{ format_date('s.started_at', '%Y%m%d') }} as integer)   as started_date_key,
    s.started_at,
    s.stopped_at,
    s.duration_minutes,
    s.energy_kwh,
    s.soc_start_pct,
    s.soc_end_pct,
    s.stop_reason,
    s.status,
    s.total_cost,
    s.currency,
    s.tariff_id,
    case when s.duration_minutes > 0
         then round(s.energy_kwh * 60.0 / s.duration_minutes, 3)
         else null end                                  as avg_power_kw,
    case when s.energy_kwh > 0
         then round(s.total_cost / s.energy_kwh, 4)
         else null end                                  as price_per_kwh,
    l_tc.h_connector_hk                                 as connector_key,
    md5(c.station_id)                                   as station_key,
    t.authorization_id,
    t.id_token
from hub h
join sat   s   on s.h_transaction_hk = h.h_transaction_hk
left join l_tc on l_tc.h_transaction_hk = h.h_transaction_hk
left join stg_t t on t.transaction_id = h.transaction_bk
left join stg_c c on c.connector_id = t.connector_id
