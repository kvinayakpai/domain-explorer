{{ config(materialized='view') }}

select
    cast(recovery_id              as varchar)    as recovery_id,
    cast(incident_id              as varchar)    as incident_id,
    cast(investigation_id         as varchar)    as investigation_id,
    cast(recovered_amount_minor   as bigint)     as recovered_amount_minor,
    cast(recovery_type            as varchar)    as recovery_type,
    cast(recovered_at             as timestamp)  as recovered_at,
    cast(recovered_by_employee_id as varchar)    as recovered_by_employee_id
from {{ source('loss_prevention', 'recovery') }}
