-- Vault hub for suspects (PII-tokenized).
{{ config(materialized='ephemeral') }}

with src as (
    select suspect_id, suspect_ref_hash, orc_ring_id, auror_offender_id, alto_packet_id
    from {{ ref('stg_loss_prevention__suspect') }}
    where suspect_id is not null
)

select
    md5(suspect_id)                       as h_suspect_hk,
    suspect_id                            as suspect_bk,
    max(suspect_ref_hash)                 as suspect_ref_hash,
    max(orc_ring_id)                      as orc_ring_id,
    max(auror_offender_id)                as auror_offender_id,
    max(alto_packet_id)                   as alto_packet_id,
    current_date                          as load_date,
    'loss_prevention.suspect'             as record_source
from src
group by suspect_id
