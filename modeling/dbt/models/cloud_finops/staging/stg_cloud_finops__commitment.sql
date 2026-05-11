{{ config(materialized='view') }}

select
    cast(commitment_id           as varchar) as commitment_id,
    cast(billing_account_id      as varchar) as billing_account_id,
    cast(commitment_type         as varchar) as commitment_type,
    cast(provider                as varchar) as provider,
    cast(service_name            as varchar) as service_name,
    cast(term_months             as integer) as term_months,
    cast(start_date              as date)    as start_date,
    cast(end_date                as date)    as end_date,
    cast(hourly_commitment_usd   as double)  as hourly_commitment_usd,
    cast(upfront_payment_usd     as double)  as upfront_payment_usd,
    cast(utilization_pct         as double)  as utilization_pct,
    cast(coverage_pct            as double)  as coverage_pct
from {{ source('cloud_finops', 'commitment') }}
