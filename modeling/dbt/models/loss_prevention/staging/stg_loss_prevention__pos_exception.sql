{{ config(materialized='view') }}

select
    cast(exception_id          as varchar)    as exception_id,
    cast(transaction_id        as varchar)    as transaction_id,
    cast(store_id              as varchar)    as store_id,
    cast(employee_id           as varchar)    as employee_id,
    cast(exception_type        as varchar)    as exception_type,
    cast(exception_score       as double)     as exception_score,
    cast(source_system         as varchar)    as source_system,
    cast(detected_at           as timestamp)  as detected_at,
    cast(status                as varchar)    as status,
    cast(amount_at_risk_minor  as bigint)     as amount_at_risk_minor,
    cast(video_segment_ref     as varchar)    as video_segment_ref,
    case when status = 'open'              then true else false end as is_open,
    case when status = 'closed_confirmed'  then true else false end as is_closed_confirmed,
    case when status = 'closed_unfounded'  then true else false end as is_closed_unfounded
from {{ source('loss_prevention', 'pos_exception') }}
