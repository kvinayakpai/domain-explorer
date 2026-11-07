-- ref.kpi.time_in_alarm: one row per drive-end vibration tag per day, flagged when
-- the day's maximum is above the tag's alarm limit (mm/s).
{{ config(materialized='table') }}

select
    d.signal_id,
    s.functional_location_id                   as functional_location_key,
    d.day,
    d.mean_value,
    d.max_value,
    s.alarm_high,
    d.max_value > s.alarm_high                 as above_alarm
from {{ ref('stg_refinery_operations__signal_daily') }} d
join {{ ref('stg_refinery_operations__signal') }} s using (signal_id)
where s.quantity = 'vibration_de'
