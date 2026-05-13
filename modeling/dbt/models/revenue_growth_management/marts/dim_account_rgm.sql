{{ config(materialized='table') }}

select
    row_number() over (order by account_id)        as account_sk,
    account_id,
    account_name,
    parent_account_id,
    channel,
    channel_tier,
    country_iso2,
    gln,
    status,
    created_at                                     as valid_from,
    cast(null as timestamp)                        as valid_to,
    true                                           as is_current
from {{ ref('stg_revenue_growth_management__accounts') }}
