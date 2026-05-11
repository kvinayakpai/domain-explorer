{{ config(materialized='view') }}

select
    cast(budget_id            as varchar) as budget_id,
    cast(billing_account_id   as varchar) as billing_account_id,
    cast(name                 as varchar) as budget_name,
    cast(period_start         as date)    as period_start,
    cast(period_end           as date)    as period_end,
    cast(budgeted_amount_usd  as double)  as budgeted_amount_usd,
    cast(actual_spend_usd     as double)  as actual_spend_usd,
    cast(forecast_amount_usd  as double)  as forecast_amount_usd,
    cast(alert_threshold_pct  as integer) as alert_threshold_pct,
    cast(alert_triggered      as boolean) as alert_triggered,
    cast(owner_email          as varchar) as owner_email,
    case when budgeted_amount_usd > 0
         then round(actual_spend_usd / budgeted_amount_usd, 4)
         else null end                    as utilization_ratio
from {{ source('cloud_finops', 'budget') }}
