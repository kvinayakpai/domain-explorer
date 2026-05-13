-- Vault sat: exception payload (insert-only descriptive context).
{{ config(materialized='ephemeral') }}

select
    md5(exception_id)                       as h_exception_hk,
    detected_at                             as load_dts,
    exception_type,
    exception_score,
    source_system,
    amount_at_risk_minor,
    status,
    video_segment_ref,
    'loss_prevention.pos_exception'         as record_source
from {{ ref('stg_loss_prevention__pos_exception') }}
