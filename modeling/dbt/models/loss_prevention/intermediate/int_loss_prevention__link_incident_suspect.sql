-- Vault link: incident <-> suspect (and incident <-> store).
{{ config(materialized='ephemeral') }}

with i as (select * from {{ ref('stg_loss_prevention__incident') }})

select
    md5(coalesce(incident_id, '') || '|' ||
        coalesce(suspect_id, '') || '|' ||
        coalesce(store_id, ''))             as l_incident_suspect_hk,
    md5(incident_id)                        as h_incident_hk,
    md5(coalesce(suspect_id, ''))           as h_suspect_hk,
    md5(store_id)                           as h_store_hk,
    current_date                            as load_date,
    'loss_prevention.incident'              as record_source
from i
where incident_id is not null
