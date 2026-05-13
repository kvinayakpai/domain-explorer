{{ config(materialized='ephemeral') }}

select distinct
    {{ dbt_utils.generate_surrogate_key(['order_id']) }}  as hk_order,
    order_id,
    current_timestamp                                     as load_dts,
    'omnichannel_oms.oms_order'                           as record_source
from {{ ref('stg_omnichannel_oms__orders') }}
