{{ config(materialized='view') }}

select
    cast(incident_id              as varchar)    as incident_id,
    cast(store_id                 as varchar)    as store_id,
    cast(incident_type            as varchar)    as incident_type,
    cast(incident_ts              as timestamp)  as incident_ts,
    cast(reported_by_employee_id  as varchar)    as reported_by_employee_id,
    cast(detected_via             as varchar)    as detected_via,
    cast(suspect_id               as varchar)    as suspect_id,
    cast(gross_loss_minor         as bigint)     as gross_loss_minor,
    cast(recovered_minor          as bigint)     as recovered_minor,
    cast(net_loss_minor           as bigint)     as net_loss_minor,
    cast(nibrs_code               as varchar)    as nibrs_code,
    cast(status                   as varchar)    as status,
    case when status = 'open'              then true else false end as is_open,
    case when status = 'closed_recovered'  then true else false end as is_closed_recovered,
    case when status = 'closed_prosecuted' then true else false end as is_closed_prosecuted,
    case when status = 'closed_writeoff'   then true else false end as is_closed_writeoff
from {{ source('loss_prevention', 'incident') }}
