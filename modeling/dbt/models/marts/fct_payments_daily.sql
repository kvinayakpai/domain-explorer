-- Daily payments fact (skeleton).
{{ config(materialized='table') }}

select
    date_trunc('day', auth_ts) as day,
    merchant_id,
    count(*) as auth_count,
    sum(case when approved then 1 else 0 end) as approved_count,
    sum(amount_minor) / 100.0 as total_amount
from {{ ref('stg_payments__authorizations') }}
group by 1, 2
