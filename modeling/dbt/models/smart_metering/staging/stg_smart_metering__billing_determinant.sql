-- Staging: light typing on smart_metering.billing_determinant.
{{ config(materialized='view') }}

select
    cast(billing_determinant_id as varchar) as billing_determinant_id,
    cast(meter_id               as varchar) as meter_id,
    cast(period_start           as date)    as period_start,
    cast(period_end             as date)    as period_end,
    cast(kwh_total              as double)  as kwh_total,
    cast(kwh_peak               as double)  as kwh_peak,
    cast(kwh_offpeak            as double)  as kwh_offpeak,
    cast(kw_demand              as double)  as kw_demand,
    cast(rate_schedule          as varchar) as rate_schedule,
    cast(estimated              as boolean) as is_estimated,
    cast({{ format_date('period_start', '%Y%m%d') }} as integer) as period_start_date_key,
    cast({{ format_date('period_end', '%Y%m%d') }} as integer) as period_end_date_key
from {{ source('smart_metering', 'billing_determinant') }}
