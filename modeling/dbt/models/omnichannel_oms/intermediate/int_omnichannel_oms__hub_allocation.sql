{{ config(materialized='ephemeral') }}

select distinct
    {{ dbt_utils.generate_surrogate_key(['allocation_id']) }} as hk_allocation,
    allocation_id,
    current_timestamp                                          as load_dts,
    'omnichannel_oms.allocation'                               as record_source
from {{ ref('stg_omnichannel_oms__allocations') }}
