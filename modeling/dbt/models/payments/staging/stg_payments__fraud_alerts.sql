-- Staging: fraud model and rule alerts on payments.
{{ config(materialized='view') }}

select
    cast(alert_id      as varchar)   as alert_id,
    cast(payment_id    as varchar)   as payment_id,
    cast(score         as double)    as score,
    cast(model_version as varchar)   as model_version,
    cast(rule_set      as varchar)   as rule_set,
    cast(raised_at     as timestamp) as raised_at,
    cast(outcome       as varchar)   as outcome
from {{ source('payments', 'fraud_alerts') }}
