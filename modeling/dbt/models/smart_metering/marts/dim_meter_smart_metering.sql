-- Meter dimension fed from the Vault hub + descriptive satellite.
-- Suffix `_smart_metering` to avoid collision with any future generic dim_meter.
{{ config(materialized='table') }}

with hub as (select * from {{ ref('int_smart_metering__hub_meter') }}),
     sat as (select * from {{ ref('int_smart_metering__sat_meter') }}),
     stg as (select * from {{ ref('stg_smart_metering__meter') }})

select
    h.h_meter_hk             as meter_key,
    h.meter_bk               as meter_id,
    s.serial_number,
    s.manufacturer,
    s.model,
    s.firmware_version,
    s.form_factor,
    s.communication_protocol,
    s.ct_ratio,
    s.status,
    g.service_point_id,
    g.installed_at,
    cast({{ dbt_utils.datediff('g.installed_at', 'current_date', 'day') }} / 365.25 as integer)
                              as fleet_age_years,
    h.load_date              as dim_loaded_at
from hub h
left join sat s on s.h_meter_hk = h.h_meter_hk
left join stg g on g.meter_id   = h.meter_bk
