{{ config(materialized='ephemeral') }}

select distinct
    {{ dbt_utils.generate_surrogate_key(['product_id']) }} as hk_product,
    product_id,
    current_timestamp                                      as load_dts,
    'omnichannel_oms.product'                              as record_source
from {{ ref('stg_omnichannel_oms__products') }}
