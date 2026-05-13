-- Vault sat: incident lifecycle state (insert-only).
{{ config(materialized='ephemeral') }}

select
    md5(incident_id)                        as h_incident_hk,
    incident_ts                             as load_dts,
    incident_type,
    status,
    gross_loss_minor,
    recovered_minor,
    net_loss_minor,
    nibrs_code,
    'loss_prevention.incident'              as record_source
from {{ ref('stg_loss_prevention__incident') }}
