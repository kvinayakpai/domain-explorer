{{ config(materialized='view') }}

select
    cast(billing_account_id    as varchar) as billing_account_id,
    cast(billing_account_name  as varchar) as billing_account_name,
    cast(provider              as varchar) as provider,
    upper(billing_currency)                as billing_currency,
    cast(payer_account_id      as varchar) as payer_account_id,
    cast(subscription_tier     as varchar) as subscription_tier,
    cast(support_level         as varchar) as support_level,
    cast(active                as boolean) as is_active
from {{ source('cloud_finops', 'billing_account') }}
