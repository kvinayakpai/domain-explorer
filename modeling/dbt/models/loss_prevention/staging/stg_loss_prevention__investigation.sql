{{ config(materialized='view') }}

select
    cast(investigation_id          as varchar)    as investigation_id,
    cast(incident_id               as varchar)    as incident_id,
    cast(opened_by_employee_id     as varchar)    as opened_by_employee_id,
    cast(opened_at                 as timestamp)  as opened_at,
    cast(closed_at                 as timestamp)  as closed_at,
    cast(investigation_type        as varchar)    as investigation_type,
    cast(status                    as varchar)    as status,
    cast(evidence_count            as integer)    as evidence_count,
    cast(video_evidence_minutes    as integer)    as video_evidence_minutes,
    cast(prosecution_referred      as boolean)    as prosecution_referred,
    cast(alto_shared               as boolean)    as alto_shared,
    cast(case_packet_uri           as varchar)    as case_packet_uri,
    case
        when closed_at is not null
            then {{ dbt_utils.datediff('opened_at', 'closed_at', 'second') }} / 3600.0
    end as duration_hours
from {{ source('loss_prevention', 'investigation') }}
