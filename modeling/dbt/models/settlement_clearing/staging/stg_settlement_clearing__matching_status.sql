-- Staging: matching status events.
{{ config(materialized='view') }}

select
    cast(matching_status_id as varchar)   as matching_status_id,
    cast(ssi_id             as varchar)   as ssi_id,
    cast(status_code        as varchar)   as status_code,
    cast(status_ts          as timestamp) as status_ts,
    cast(reason_code        as varchar)   as reason_code,
    cast(matched_party_id   as varchar)   as matched_party_id
from {{ source('settlement_clearing', 'matching_status') }}
