{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['pack_id']) }}      as hk_pack,
    pack_id,
    current_timestamp                                         as load_dts,
    'revenue_growth_management.pack'                           as record_source
from {{ ref('stg_revenue_growth_management__packs') }}
