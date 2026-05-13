{{ config(materialized='ephemeral') }}

select
    {{ dbt_utils.generate_surrogate_key(['order_id']) }} as hk_order,
    captured_at                                          as load_dts,
    capture_channel,
    payment_status,
    order_status,
    promise_delivery_ts,
    closed_at,
    'omnichannel_oms.oms_order'                          as record_source
from {{ ref('stg_omnichannel_oms__orders') }}
