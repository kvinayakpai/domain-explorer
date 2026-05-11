{{ config(materialized='view') }}

select
    cast(audit_id            as varchar)   as audit_id,
    cast(return_id           as varchar)   as return_id,
    cast(audit_type          as varchar)   as audit_type,
    cast(selection_reason    as varchar)   as selection_reason,
    cast(opened_at           as timestamp) as opened_at,
    cast(closed_at           as timestamp) as closed_at,
    cast(examiner_id         as varchar)   as examiner_id,
    cast(proposed_adjustment as double)    as proposed_adjustment,
    cast(outcome             as varchar)   as outcome,
    case
        when opened_at is not null and closed_at is not null
            then {{ dbt_utils.datediff('opened_at', 'closed_at', 'day') }}
    end as resolution_days
from {{ source('tax_administration', 'audit') }}
