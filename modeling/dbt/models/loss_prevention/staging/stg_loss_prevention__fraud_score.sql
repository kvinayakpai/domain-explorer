{{ config(materialized='view') }}

select
    cast(fraud_score_id    as varchar)    as fraud_score_id,
    cast(customer_ref_hash as varchar)    as customer_ref_hash,
    cast(transaction_id    as varchar)    as transaction_id,
    cast(score_source      as varchar)    as score_source,
    cast(score             as double)     as score,
    cast(recommendation    as varchar)    as recommendation,
    cast(scored_at         as timestamp)  as scored_at
from {{ source('loss_prevention', 'fraud_score') }}
