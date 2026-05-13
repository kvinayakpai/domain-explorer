{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['a.allocation_id','a.order_line_id','a.location_id']) }} as hk_link,
    {{ dbt_utils.generate_surrogate_key(['a.allocation_id']) }} as hk_allocation,
    {{ dbt_utils.generate_surrogate_key(['a.order_line_id']) }} as hk_order_line,
    {{ dbt_utils.generate_surrogate_key(['a.location_id']) }}   as hk_location,
    {{ dbt_utils.generate_surrogate_key(['a.rule_id']) }}       as hk_rule,
    current_timestamp                                            as load_dts,
    'omnichannel_oms.allocation'                                 as record_source
from {{ ref('stg_omnichannel_oms__allocations') }} a
