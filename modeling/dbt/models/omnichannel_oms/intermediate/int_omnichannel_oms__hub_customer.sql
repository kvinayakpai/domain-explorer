{{ config(materialized='ephemeral') }}

select distinct
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as hk_customer,
    customer_id,
    current_timestamp                                       as load_dts,
    'omnichannel_oms.customer'                              as record_source
from {{ ref('stg_omnichannel_oms__customers') }}
