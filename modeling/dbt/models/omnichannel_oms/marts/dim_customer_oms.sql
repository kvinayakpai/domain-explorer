{{ config(materialized='table') }}

select
    row_number() over (order by customer_id) as customer_sk,
    customer_id,
    golden_record_id,
    home_country_iso2,
    has_loyalty,
    status,
    created_at                                as valid_from,
    cast(null as timestamp)                   as valid_to,
    true                                      as is_current
from {{ ref('stg_omnichannel_oms__customers') }}
