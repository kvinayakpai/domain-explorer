-- Staging: failed settlement events with CSDR penalty.
{{ config(materialized='view') }}

select
    cast(failure_id                as varchar)   as failure_id,
    cast(ssi_id                    as varchar)   as ssi_id,
    cast(fail_reason               as varchar)   as fail_reason,
    cast(failed_at                 as timestamp) as failed_at,
    cast(estimated_resolution_date as date)      as estimated_resolution_date,
    cast(csdr_penalty_amount       as double)    as csdr_penalty_amount,
    cast(status                    as varchar)   as status
from {{ source('settlement_clearing', 'failed_settlement') }}
