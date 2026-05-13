-- Vault link: Failure Event ↔ Asset ↔ Failure Mode.
{{ config(materialized='ephemeral') }}

with f as (
    select failure_event_id, asset_id, failure_mode_id
    from {{ ref('stg_predictive_maintenance__failure_event') }}
    where failure_event_id is not null
)

select
    md5(failure_event_id || '|' || coalesce(asset_id, '') || '|' || coalesce(failure_mode_id, '')) as l_failure_asset_hk,
    md5(failure_event_id)                       as h_failure_event_hk,
    md5(asset_id)                               as h_asset_hk,
    md5(failure_mode_id)                        as h_failure_mode_hk,
    current_date                                as load_date,
    'predictive_maintenance.failure_event'      as record_source
from f
group by failure_event_id, asset_id, failure_mode_id
