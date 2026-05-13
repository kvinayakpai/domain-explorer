{{ config(materialized='ephemeral') }}

with src as (select * from {{ ref('stg_direct_store_delivery__stop') }})

select
    md5(stop_id)                                                                                                                                as h_stop_hk,
    current_timestamp                                                                                                                            as load_ts,
    md5(coalesce(status,'') || '|' || cast(coalesce(actual_sequence,0) as varchar) || '|' || cast(coalesce(actual_arrival, timestamp '1900-01-01') as varchar)) as hashdiff,
    planned_sequence,
    actual_sequence,
    planned_arrival,
    actual_arrival,
    planned_departure,
    actual_departure,
    arrival_minutes_delta,
    dwell_minutes,
    status,
    skip_reason,
    is_completed,
    is_skipped,
    'direct_store_delivery.stop'                                                                                                                 as record_source
from src
