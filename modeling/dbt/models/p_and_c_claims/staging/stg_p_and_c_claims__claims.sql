-- Staging: claim header — one row per claim with FNOL through close metadata.
{{ config(materialized='view') }}

select
    cast(claim_id        as varchar)   as claim_id,
    cast(policy_id       as varchar)   as policy_id,
    cast(adjuster_id     as varchar)   as adjuster_id,
    cast(fnol_ts         as timestamp) as fnol_ts,
    cast(loss_date       as timestamp) as loss_date,
    cast(peril           as varchar)   as peril,
    cast(severity        as varchar)   as severity,
    cast(status          as varchar)   as claim_status,
    cast(incurred_amount as double)    as incurred_amount,
    cast(fraud_score     as double)    as fraud_score,
    case
        when cast(fnol_ts as timestamp) is not null
         and cast(loss_date as timestamp) is not null
            then {{ dbt_utils.datediff('cast(loss_date as timestamp)', 'cast(fnol_ts as timestamp)', 'day') }}
    end                                as report_lag_days
from {{ source('p_and_c_claims', 'claims') }}
