{{ config(materialized='table') }}

select
    row_number() over (order by price_list_id) as price_list_sk,
    price_list_id,
    pack_id,
    account_id,
    list_price_cents,
    srp_cents,
    currency,
    effective_from,
    effective_to,
    source_system,
    case when status = 'active' then true else false end as is_current
from {{ ref('stg_revenue_growth_management__price_lists') }}
