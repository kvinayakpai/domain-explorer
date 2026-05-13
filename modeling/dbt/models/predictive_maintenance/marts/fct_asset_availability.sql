-- Daily asset-availability fact. Drives MTBF, MTTR, Asset Availability %.
-- Synthetic computation — combines failure_events and work_orders by date.
{{ config(materialized='table') }}

with date_grid as (
    select d.cal_date, d.date_key, a.asset_sk, a.asset_id
    from {{ ref('dim_date_pm') }} d
    cross join {{ ref('dim_asset_pm') }} a
    where d.cal_date between cast('2026-05-01' as date) and cast('2026-05-07' as date)
),
fail as (
    select
        asset_id,
        cast(failure_ts as date) as fail_date,
        count(*)               as failure_count,
        sum(downtime_minutes)  as unplanned_downtime_min
    from {{ ref('stg_predictive_maintenance__failure_event') }}
    group by 1, 2
),
wo as (
    select
        asset_id,
        cast(scheduled_start as date) as wo_date,
        sum(case when is_planned     then coalesce(repair_minutes, 0) else 0 end) as planned_downtime_min,
        sum(case when is_corrective  then coalesce(repair_minutes, 0) else 0 end) as repair_minutes_total
    from {{ ref('stg_predictive_maintenance__work_order') }}
    group by 1, 2
)

select
    cast(md5(g.asset_id || '|' || cast(g.cal_date as varchar)) as varchar) as asset_availability_id,
    g.date_key,
    g.asset_sk,
    1440                                                                   as scheduled_minutes,
    1440 - coalesce(fail.unplanned_downtime_min, 0) - coalesce(wo.planned_downtime_min, 0) as runtime_minutes,
    coalesce(wo.planned_downtime_min, 0)                                   as planned_downtime_min,
    coalesce(fail.unplanned_downtime_min, 0)                               as unplanned_downtime_min,
    coalesce(fail.failure_count, 0)                                        as failure_count,
    coalesce(wo.repair_minutes_total, 0)                                   as repair_minutes_total,
    case
        when 1440 = 0 then 0
        else cast(
            (1440 - coalesce(fail.unplanned_downtime_min, 0))::double / 1440
            as numeric(7,4))
    end                                                                    as availability_pct,
    case
        when coalesce(fail.failure_count, 0) = 0 then null
        else cast(
            ((1440 - coalesce(fail.unplanned_downtime_min, 0))::double / 60.0)
            / coalesce(fail.failure_count, 1) as numeric(12,4))
    end                                                                    as mtbf_hours,
    case
        when coalesce(fail.failure_count, 0) = 0 then null
        else cast(
            coalesce(wo.repair_minutes_total, 0)::double
            / coalesce(fail.failure_count, 1) as numeric(12,4))
    end                                                                    as mttr_minutes
from date_grid g
left join fail on fail.asset_id = g.asset_id and fail.fail_date = g.cal_date
left join wo   on wo.asset_id   = g.asset_id and wo.wo_date    = g.cal_date
