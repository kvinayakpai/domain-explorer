{{ config(materialized='table') }}

select
    row_number() over (order by customer_id)        as customer_sk,
    customer_id,
    customer_ref_hash,
    country_iso2,
    loyalty_tier,
    lifetime_orders,
    lifetime_returns,
    chronic_returner_flag,
    chronic_returner_score,
    status,
    created_at                                       as valid_from,
    cast(null as timestamp)                          as valid_to,
    true                                             as is_current
from {{ ref('stg_returns_reverse_logistics__customers') }}
