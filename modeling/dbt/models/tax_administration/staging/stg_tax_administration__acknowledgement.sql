{{ config(materialized='view') }}

select
    cast(ack_id          as varchar)   as ack_id,
    cast(transmission_id as varchar)   as transmission_id,
    cast(submission_id   as varchar)   as submission_id,
    cast(ack_status      as varchar)   as ack_status,
    cast(ack_ts          as timestamp) as ack_ts,
    cast(error_codes     as varchar)   as error_codes,
    cast(error_message   as varchar)   as error_message,
    case when ack_status = 'A' then true else false end as is_accepted,
    case when ack_status = 'R' then true else false end as is_rejected
from {{ source('tax_administration', 'acknowledgement') }}
