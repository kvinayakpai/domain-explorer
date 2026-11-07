-- ref.kpi.pump_mtbf, ref.kpi.failures_per_pump_year and ref.kpi.lot_failure_ratio:
-- installed time and failures per bearing lot, against the whole fleet.
{{ config(materialized='table') }}

with inst as (
        select i.equipment_key, i.installed_days, i.failure_count, e.bearing_lot_id, e.bearing_lot_waived
        from {{ ref('fct_installation_ro') }} i
        join {{ ref('dim_equipment_ro') }} e using (equipment_key)
     ),
     fleet as (
        select sum(failure_count) / (sum(installed_days) / 365.0) as fleet_failures_per_pump_year
        from inst
     ),
     by_lot as (
        select
            coalesce(bearing_lot_id, 'no maker genealogy') as bearing_lot_id,
            bool_or(coalesce(bearing_lot_waived, false))   as qualification_waived,
            count(distinct equipment_key)                  as pumps,
            sum(installed_days)                            as installed_days,
            sum(failure_count)                             as failures
        from inst
        group by 1
     )

select
    b.bearing_lot_id,
    b.qualification_waived,
    b.pumps,
    b.installed_days,
    b.failures,
    round(b.installed_days / 365.0, 2)                              as pump_years,
    round(b.failures / (b.installed_days / 365.0), 3)               as failures_per_pump_year,
    case when b.failures > 0 then round(b.installed_days * 1.0 / b.failures, 0) end as mtbf_days,
    round((b.failures / (b.installed_days / 365.0)) / fleet.fleet_failures_per_pump_year, 2) as lot_failure_ratio,
    -- a lot seen on one pump for a year says little; read the ratio only with real exposure
    b.installed_days / 365.0 >= 5                                   as enough_exposure
from by_lot b
cross join fleet
where b.installed_days > 0
order by failures_per_pump_year desc
