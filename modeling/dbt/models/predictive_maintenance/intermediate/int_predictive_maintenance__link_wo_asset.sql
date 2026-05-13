-- Vault link: Work Order ↔ Asset ↔ Failure Event (when corrective).
{{ config(materialized='ephemeral') }}

with w as (
    select work_order_id, asset_id, failure_event_id
    from {{ ref('stg_predictive_maintenance__work_order') }}
    where work_order_id is not null
)

select
    md5(work_order_id || '|' || coalesce(asset_id, '') || '|' || coalesce(failure_event_id, '')) as l_wo_asset_hk,
    md5(work_order_id)                          as h_work_order_hk,
    md5(asset_id)                               as h_asset_hk,
    case when failure_event_id is not null then md5(failure_event_id) end as h_failure_event_hk,
    current_date                                as load_date,
    'predictive_maintenance.work_order'         as record_source
from w
group by work_order_id, asset_id, failure_event_id
