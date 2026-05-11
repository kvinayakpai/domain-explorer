-- Grain: one row per budget period.
{{ config(materialized='table') }}

with b as (select * from {{ ref('stg_cloud_finops__budget') }})

select
    md5(b.budget_id)                                       as budget_key,
    b.budget_id,
    md5(b.billing_account_id)                              as billing_account_key,
    b.billing_account_id,
    b.budget_name,
    b.period_start,
    b.period_end,
    cast({{ format_date('b.period_start', '%Y%m%d') }} as integer)    as period_start_date_key,
    b.budgeted_amount_usd,
    b.actual_spend_usd,
    b.forecast_amount_usd,
    b.utilization_ratio,
    b.actual_spend_usd - b.budgeted_amount_usd             as variance_usd,
    b.alert_threshold_pct,
    b.alert_triggered,
    b.owner_email
from b
