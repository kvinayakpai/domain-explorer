-- Vault hub for investigations.
{{ config(materialized='ephemeral') }}

with src as (
    select investigation_id
    from {{ ref('stg_loss_prevention__investigation') }}
    where investigation_id is not null
)

select
    md5(investigation_id)               as h_investigation_hk,
    investigation_id                    as investigation_bk,
    current_date                        as load_date,
    'loss_prevention.investigation'     as record_source
from src
group by investigation_id
