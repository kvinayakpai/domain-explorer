{{ config(materialized='view') }}

-- High-cardinality time-series. Keep as a view so dbt doesn't materialize 50M rows.
-- Downstream marts pre-aggregate.
select
    cast(reading_id     as bigint)    as reading_id,
    cast(sensor_id      as varchar)   as sensor_id,
    cast(asset_id       as varchar)   as asset_id,
    cast(reading_ts     as timestamp) as reading_ts,
    cast(value          as double)    as value,
    cast(quality_code   as smallint)  as quality_code,
    cast(is_anomaly     as boolean)   as is_anomaly,
    cast(ingestion_ts   as timestamp) as ingestion_ts,
    case when quality_code = 192 then true else false end as is_good_quality
from {{ source('predictive_maintenance', 'sensor_reading') }}
