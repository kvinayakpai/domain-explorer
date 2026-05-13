{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['deal_id']) }}      as hk_deal,
    deal_id,
    current_timestamp                                         as load_dts,
    'revenue_growth_management.deal'                           as record_source
from {{ ref('stg_revenue_growth_management__deals') }}
