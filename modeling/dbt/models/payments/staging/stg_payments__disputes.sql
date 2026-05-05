-- Staging: customer/issuer disputes attached to chargebacks.
{{ config(materialized='view') }}

select
    cast(dispute_id    as varchar)   as dispute_id,
    cast(chargeback_id as varchar)   as chargeback_id,
    cast(opened_ts     as timestamp) as opened_ts,
    cast(category      as varchar)   as category,
    cast(amount        as double)    as amount,
    cast(resolved_ts   as timestamp) as resolved_ts,
    cast(status        as varchar)   as status,
    case
        when resolved_ts is not null
            then date_diff('day', opened_ts, resolved_ts)
    end                              as resolution_days
from {{ source('payments', 'disputes') }}
