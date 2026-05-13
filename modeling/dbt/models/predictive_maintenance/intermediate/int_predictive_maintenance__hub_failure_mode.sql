-- Vault hub for the Failure Mode business key.
{{ config(materialized='ephemeral') }}

with src as (
    select failure_mode_id, fault_code
    from {{ ref('stg_predictive_maintenance__failure_mode') }}
    where failure_mode_id is not null
)

select
    md5(failure_mode_id)                        as h_failure_mode_hk,
    failure_mode_id                             as failure_mode_bk,
    max(fault_code)                             as fault_code,
    current_date                                as load_date,
    'predictive_maintenance.failure_mode'       as record_source
from src
group by failure_mode_id
