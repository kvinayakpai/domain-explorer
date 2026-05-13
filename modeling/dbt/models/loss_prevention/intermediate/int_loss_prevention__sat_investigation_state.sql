-- Vault sat: investigation lifecycle state.
{{ config(materialized='ephemeral') }}

select
    md5(investigation_id)                   as h_investigation_hk,
    opened_at                               as load_dts,
    investigation_type,
    status,
    evidence_count,
    video_evidence_minutes,
    prosecution_referred,
    alto_shared,
    case_packet_uri,
    'loss_prevention.investigation'         as record_source
from {{ ref('stg_loss_prevention__investigation') }}
