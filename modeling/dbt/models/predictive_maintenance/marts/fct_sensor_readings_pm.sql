-- Hourly-grain pre-aggregation of sensor_reading.
-- The raw minute-level source view (50M+ rows at medium scale) stays as-is;
-- this mart rolls up to hourly stats (avg / min / max / stddev) — the form
-- BI typically consumes. Suffix `_pm` to avoid collision with any other anchor.
{{ config(materialized='table') }}

with r as (
    select
        sensor_id,
        asset_id,
        date_trunc('hour', reading_ts) as reading_hour,
        value,
        is_good_quality,
        is_anomaly
    from {{ ref('stg_predictive_maintenance__sensor_reading') }}
),
agg as (
    select
        sensor_id,
        asset_id,
        reading_hour,
        count(*)                                                   as sample_count,
        avg(value)                                                 as value_avg,
        max(value)                                                 as value_max,
        min(value)                                                 as value_min,
        stddev_pop(value)                                          as value_stddev,
        sum(case when is_good_quality then 1 else 0 end) * 1.0
            / nullif(count(*), 0)                                  as pct_good_quality,
        sum(case when is_anomaly then 1 else 0 end)                as anomaly_count
    from r
    group by 1, 2, 3
)

select
    -- Stable surrogate per (sensor, hour) — md5 hex truncated for compactness.
    cast(substr(md5(sensor_id || '|' || cast(reading_hour as varchar)), 1, 16) as varchar) as reading_id,
    cast({{ format_date('cast(reading_hour as date)', '%Y%m%d') }} as integer)              as date_key,
    a.asset_sk,
    s.sensor_sk,
    agg.reading_hour,
    agg.sample_count,
    agg.value_avg,
    agg.value_max,
    agg.value_min,
    agg.value_stddev,
    agg.pct_good_quality,
    agg.anomaly_count
from agg
left join {{ ref('dim_asset_pm') }} a on a.asset_id = agg.asset_id
left join {{ ref('dim_sensor') }}    s on s.sensor_id = agg.sensor_id
