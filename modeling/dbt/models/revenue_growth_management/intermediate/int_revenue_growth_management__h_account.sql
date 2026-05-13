-- Vault hub for account business keys (sketch — materialized=ephemeral in dbt_project).
{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['account_id']) }} as hk_account,
    account_id,
    current_timestamp                                       as load_dts,
    'revenue_growth_management.account'                      as record_source
from {{ ref('stg_revenue_growth_management__accounts') }}
