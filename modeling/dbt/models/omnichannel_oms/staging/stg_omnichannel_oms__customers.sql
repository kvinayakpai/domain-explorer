{{ config(materialized='view') }}

select
    cast(customer_id        as varchar)    as customer_id,
    cast(golden_record_id   as varchar)    as golden_record_id,
    cast(email_hash         as varchar)    as email_hash,
    cast(phone_hash         as varchar)    as phone_hash,
    cast(loyalty_id         as varchar)    as loyalty_id,
    upper(home_country_iso2)                as home_country_iso2,
    cast(created_at         as timestamp)  as created_at,
    cast(status             as varchar)    as status,
    case when loyalty_id is not null then true else false end as has_loyalty
from {{ source('omnichannel_oms', 'customer') }}
