{{ config(materialized='view') }}

select
    cast(suspect_id              as varchar)    as suspect_id,
    cast(suspect_ref_hash        as varchar)    as suspect_ref_hash,
    cast(alias_count             as smallint)   as alias_count,
    cast(first_seen_at           as timestamp)  as first_seen_at,
    cast(last_seen_at            as timestamp)  as last_seen_at,
    cast(orc_flag                as boolean)    as orc_flag,
    cast(orc_ring_id             as varchar)    as orc_ring_id,
    cast(known_vehicle_ref_hash  as varchar)    as known_vehicle_ref_hash,
    cast(auror_offender_id       as varchar)    as auror_offender_id,
    cast(alto_packet_id          as varchar)    as alto_packet_id
from {{ source('loss_prevention', 'suspect') }}
