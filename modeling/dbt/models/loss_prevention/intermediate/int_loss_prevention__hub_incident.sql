-- Vault hub for incidents.
{{ config(materialized='ephemeral') }}

with src as (
    select incident_id
    from {{ ref('stg_loss_prevention__incident') }}
    where incident_id is not null
)

select
    md5(incident_id)                    as h_incident_hk,
    incident_id                         as incident_bk,
    current_date                        as load_date,
    'loss_prevention.incident'          as record_source
from src
group by incident_id
