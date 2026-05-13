-- Customer dimension for the CDP analytics layer. Type-2 framing.
-- Suffix `_cdp` avoids collision with customer_analytics + loyalty dim_customer.
{{ config(materialized='table') }}

select
    row_number() over (order by customer_id)        as customer_sk,
    customer_id,
    email_sha256,
    phone_sha256,
    country_iso2,
    postal_code,
    lifecycle_stage,
    rfm_recency,
    rfm_frequency,
    rfm_monetary,
    predicted_clv,
    predicted_churn_prob,
    golden_record_source,
    confidence_score,
    resolution_method,
    status,
    created_at                                       as valid_from,
    cast(null as timestamp)                          as valid_to,
    true                                             as is_current
from {{ ref('stg_customer_loyalty_cdp__customer_master') }}
