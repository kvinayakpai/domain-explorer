{{ config(materialized='view') }}

select
    cast(customer_id            as varchar)    as customer_id,
    cast(first_name_token       as varchar)    as first_name_token,
    cast(last_name_token        as varchar)    as last_name_token,
    cast(email_sha256           as varchar)    as email_sha256,
    cast(phone_sha256           as varchar)    as phone_sha256,
    cast(country_iso2           as varchar)    as country_iso2,
    cast(postal_code            as varchar)    as postal_code,
    cast(golden_record_source   as varchar)    as golden_record_source,
    cast(confidence_score       as double)     as confidence_score,
    cast(resolution_method      as varchar)    as resolution_method,
    cast(lifecycle_stage        as varchar)    as lifecycle_stage,
    cast(rfm_recency            as smallint)   as rfm_recency,
    cast(rfm_frequency          as smallint)   as rfm_frequency,
    cast(rfm_monetary           as smallint)   as rfm_monetary,
    cast(predicted_clv          as double)     as predicted_clv,
    cast(predicted_churn_prob   as double)     as predicted_churn_prob,
    cast(first_seen_at          as timestamp)  as first_seen_at,
    cast(last_seen_at           as timestamp)  as last_seen_at,
    cast(created_at             as timestamp)  as created_at,
    cast(updated_at             as timestamp)  as updated_at,
    cast(status                 as varchar)    as status
from {{ source('customer_loyalty_cdp', 'customer_master') }}
