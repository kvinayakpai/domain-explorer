{{ config(materialized='view') }}

select
    cast(membership_id   as varchar)    as membership_id,
    cast(customer_id     as varchar)    as customer_id,
    cast(segment_id      as varchar)    as segment_id,
    cast(entered_at      as timestamp)  as entered_at,
    cast(exited_at       as timestamp)  as exited_at,
    cast(entry_reason    as varchar)    as entry_reason,
    cast(source_system   as varchar)    as source_system,
    cast(is_current      as boolean)    as is_current,
    case
        when exited_at is not null
            then {{ dbt_utils.datediff('entered_at', 'exited_at', 'second') }}
    end                                  as duration_seconds
from {{ source('customer_loyalty_cdp', 'segment_membership') }}
