{{ config(materialized='view') }}

select
    cast(transmission_id     as varchar)   as transmission_id,
    cast(submission_id       as varchar)   as submission_id,
    cast(return_id           as varchar)   as return_id,
    cast(ero_id              as varchar)   as ero_id,
    cast(transmitter_id      as varchar)   as transmitter_id,
    cast(sent_at             as timestamp) as sent_at,
    cast(received_at         as timestamp) as received_at,
    cast(envelope_format     as varchar)   as envelope_format,
    cast(byte_size           as bigint)    as byte_size,
    cast(transmission_status as varchar)   as transmission_status,
    case
        when sent_at is not null and received_at is not null
            then {{ dbt_utils.datediff('sent_at', 'received_at', 'second') }}
    end as transit_seconds
from {{ source('tax_administration', 'transmission') }}
