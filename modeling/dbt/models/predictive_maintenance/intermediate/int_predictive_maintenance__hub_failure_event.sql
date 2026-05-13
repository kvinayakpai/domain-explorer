-- Vault hub for the Failure Event business key.
{{ config(materialized='ephemeral') }}

with src as (
    select failure_event_id
    from {{ ref('stg_predictive_maintenance__failure_event') }}
    where failure_event_id is not null
)

select
    md5(failure_event_id)                       as h_failure_event_hk,
    failure_event_id                            as failure_event_bk,
    current_date                                as load_date,
    'predictive_maintenance.failure_event'      as record_source
from src
group by failure_event_id
