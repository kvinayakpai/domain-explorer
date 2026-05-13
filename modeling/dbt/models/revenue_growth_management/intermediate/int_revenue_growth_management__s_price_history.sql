-- Vault satellite — insert-only price history per price_list_id × load_dts.
{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['price_list_id']) }}  as hk_price_list,
    recorded_at                                                  as load_dts,
    price_list_id,
    pack_id,
    account_id,
    list_price_cents,
    srp_cents,
    currency,
    effective_from,
    effective_to,
    source_system,
    status,
    'revenue_growth_management.price_list'                       as record_source
from {{ ref('stg_revenue_growth_management__price_lists') }}
