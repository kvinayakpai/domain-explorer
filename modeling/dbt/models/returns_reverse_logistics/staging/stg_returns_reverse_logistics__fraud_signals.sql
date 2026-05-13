{{ config(materialized='view') }}

select
    cast(fraud_signal_id  as varchar)    as fraud_signal_id,
    cast(rma_id           as varchar)    as rma_id,
    cast(customer_id      as varchar)    as customer_id,
    cast(source           as varchar)    as source,
    cast(signal_type      as varchar)    as signal_type,
    cast(score            as double)     as score,
    cast(recommendation   as varchar)    as recommendation,
    cast(scored_at        as timestamp)  as scored_at,
    case when recommendation = 'deny' then true else false end as is_denied,
    case when recommendation = 'stepup_required' then true else false end as is_stepup
from {{ source('returns_reverse_logistics', 'fraud_signal') }}
