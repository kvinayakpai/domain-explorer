{{ config(materialized='view') }}

select
    cast(customer_id              as varchar)    as customer_id,
    cast(customer_ref_hash        as varchar)    as customer_ref_hash,
    upper(country_iso2)                           as country_iso2,
    cast(loyalty_tier             as varchar)    as loyalty_tier,
    cast(lifetime_orders          as integer)    as lifetime_orders,
    cast(lifetime_returns         as integer)    as lifetime_returns,
    cast(chronic_returner_flag    as boolean)    as chronic_returner_flag,
    cast(chronic_returner_score   as double)     as chronic_returner_score,
    cast(status                   as varchar)    as status,
    cast(created_at               as timestamp)  as created_at
from {{ source('returns_reverse_logistics', 'customer') }}
